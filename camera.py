import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import logging
import paho.mqtt.client as mqtt
from mqtt_topics import Topics  # Import Topics enum
from mqtt_payload import create_payload, publish_payload  # Import helper functions
import time
import json

# ----------- KONFIGURATION -----------
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
PICTURE_FOLDER = Path(__file__).parent / "pics"
LATEST_PICTURE_TOPIC = Topics.SEND_LATEST_PICTURES.value  # Use Topics enum

# ----------- LOGGING -----------
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
today_log_file = LOG_DIR / f"camera_{datetime.now().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ----------- MQTT CLIENT -----------
client = mqtt.Client()

def setup_mqtt():
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")
        exit(1)

# ----------- CAMERA SETUP -----------
def take_picture(delays=None):
    """
    Takes multiple pictures according to the 'delays' array. 
    If delays = [1,1,1,10], it will:
    1. Sleep 1s, take picture
    2. Sleep 1s, take picture
    3. Sleep 1s, take picture
    4. Sleep 10s, take final picture
    If no array or empty array is provided, capture once.
    """
    captured_pictures = []

    def capture_picture():
        try:
            PICTURE_FOLDER.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            picture_path = PICTURE_FOLDER / f"{timestamp}.jpg"

            # Use libcamera-still to capture the image
            command = [
                "libcamera-still",
                "--nopreview",
                "-o", str(picture_path),
                "--width", "1280",  # Lower resolution => faster capture
                "--height", "720",
                "--timeout", "100"  # 0.1 seconds
            ]
            subprocess.run(command, check=True)
            logger.info(f"Picture taken and saved to {picture_path}")

            # Add overlay text with a black background
            text_overlay = f"SEAHUT57 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.Popen([
                "convert",
                str(picture_path),
                "-pointsize", "32",
                "-fill", "white",
                "-undercolor", "black",
                "-gravity", "SouthWest",
                "-annotate", "+10+40",
                text_overlay,
                str(picture_path)
            ])
            logger.info(f"Started overlay in background for {picture_path}")

            # Store the path of the captured picture
            captured_pictures.append(str(picture_path))
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to take picture with libcamera-still: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while taking picture: {e}")

    if not delays:
        capture_picture()
        payload = create_payload(
            source="camera",
            event="TAKE_PICTURE",
            data={"pictures": captured_pictures}
        )
        publish_payload(Topics.SEND_LATEST_PICTURES.value, payload)
        logger.info(f"Published captured picture path to topic '{Topics.SEND_LATEST_PICTURES.value}'")
        return

    for d in delays:
        if d > 0:
            time.sleep(d)
        capture_picture()

    # After all captures are done, publish them together
    payload = create_payload(
        source="camera",
        event="TAKE_PICTURE",
        data={"pictures": captured_pictures}
    )
    publish_payload(Topics.SEND_LATEST_PICTURES.value, payload)
    logger.info(f"Published all captured picture paths to topic '{Topics.SEND_LATEST_PICTURES.value}'")

# ----------- CALLBACKS -----------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Successfully connected to MQTT broker.")
        # Subscribe to the TAKE_PICTURE topic
        client.subscribe(Topics.TAKE_PICTURE.value)
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")

def on_message(client, userdata, msg):
    logger.info(f"Message received on topic '{msg.topic}': {msg.payload.decode()}")
    if msg.topic == Topics.TAKE_PICTURE.value:
        try:
            data = json.loads(msg.payload.decode())
            sequence = data.get("data", {}).get("sequence", [])
            take_picture(delays=sequence)
        except Exception as e:
            logger.error(f"Failed to extract sequence from payload: {e}")

# ----------- MAIN LOOP -----------
def main():
    setup_mqtt()
    client.on_connect = on_connect
    client.on_message = on_message

    logger.info("Starting camera service...")
    client.loop_forever()

if __name__ == "__main__":
    main()
