import sys
import os
import time
import threading
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from mqtt_topics import Topics  # Import Topics enum
from mqtt_payload import create_payload, publish_payload  # Import helper functions
from mqtt_client import get_mqtt_client  # Import the singleton MQTT client

# ----------- KONFIGURATION -----------
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

# Ensure the logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# ----------- LOGGNING -----------
today_log_file = os.path.join(LOG_DIR, f"controller_{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------- MQTT CLIENT -----------
client = get_mqtt_client()
if client is None:
    logger.error("Failed to initialize MQTT client. Exiting...")
    sys.exit(1)

# ----------- CALLBACKS -----------
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("Successfully connected to MQTT broker.")
        # Subscribe to PIR motion topics
        client.subscribe([
            (Topics.PIR_MOTION_DETECTED.value, 0),
            (Topics.PIR_MOTION_ENDED.value, 0)
        ])
        logger.info(f"Subscribed to topics: {Topics.PIR_MOTION_DETECTED.value}, {Topics.PIR_MOTION_ENDED.value}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")

def schedule_capture(delay_seconds):
    threading.Timer(delay_seconds, trigger_picture_capture).start()

def start_motion_capture_sequence():
    schedule_capture(0)
    schedule_capture(1)
    schedule_capture(2)
    schedule_capture(12)

def on_message(client, userdata, msg):
    logger.info(f"Message received on topic '{msg.topic}': {msg.payload.decode()}")
    if msg.topic == Topics.PIR_MOTION_DETECTED.value:
        logger.info("Motion detected! Triggering picture capture in a separate thread...")
        start_motion_capture_sequence()

def trigger_picture_capture():
    """
    Publishes a message to the TAKE_PICTURE topic to trigger the camera.
    """
    try:
        payload = create_payload(source="controller", event="TAKE_PICTURE")
        publish_payload(Topics.TAKE_PICTURE.value, payload)
        logger.info(f"Published TAKE_PICTURE event to topic '{Topics.TAKE_PICTURE.value}'")
    except Exception as e:
        logger.error(f"Failed to trigger picture capture: {e}")

# ----------- MAIN LOOP -----------
def main():
    client.on_connect = on_connect
    client.on_message = on_message

    logger.info("Starting controller...")
    client.loop_forever()

if __name__ == "__main__":
    main()
