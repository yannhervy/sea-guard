import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import paho.mqtt.client as mqtt
from datetime import datetime
from pathlib import Path
from picamera import PiCamera
from mqtt_topics import Topics  # Import Topics enum
from mqtt_payload import create_payload, publish_payload  # Import helper functions

# ----------- KONFIGURATION -----------
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
PICTURE_FOLDER = Path(__file__).parent / "pics"
LATEST_PICTURE_TOPIC = "LATEST_PICTURE_TAKEN"  # Define topic for latest picture

# ----------- LOGGNING -----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("camera.log"),
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
camera = PiCamera()

def take_picture():
    """
    Captures an image, saves it to the PICTURE_FOLDER, and publishes its path.
    """
    try:
        PICTURE_FOLDER.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        picture_path = PICTURE_FOLDER / f"{timestamp}.jpg"
        camera.capture(str(picture_path))
        logger.info(f"Picture taken and saved to {picture_path}")

        # Publish the path of the latest picture
        payload = create_payload(source="camera", event="PICTURE_TAKEN", data={"path": str(picture_path)})
        publish_payload(client, LATEST_PICTURE_TOPIC, payload)
        logger.info(f"Published latest picture path to topic '{LATEST_PICTURE_TOPIC}'")
    except Exception as e:
        logger.error(f"Failed to take picture: {e}")

# ----------- CALLBACKS -----------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Successfully connected to MQTT broker.")
        # Subscribe to the TAKE_PICTURE topic
        client.subscribe(Topics.PICTURE_TAKEN.value)
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")

def on_message(client, userdata, msg):
    logger.info(f"Message received on topic '{msg.topic}': {msg.payload.decode()}")
    if msg.topic == Topics.PICTURE_TAKEN.value:
        logger.info("TAKE_PICTURE command received. Capturing image...")
        take_picture()

# ----------- MAIN LOOP -----------
def main():
    setup_mqtt()
    client.on_connect = on_connect
    client.on_message = on_message

    logger.info("Starting camera service...")
    client.loop_forever()

if __name__ == "__main__":
    main()
