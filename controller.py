import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import paho.mqtt.client as mqtt
from mqtt_topics import Topics  # Import Topics enum
from mqtt_payload import create_payload, publish_payload  # Import helper functions
from datetime import datetime

# ----------- KONFIGURATION -----------
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# ----------- LOGGNING -----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("controller.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------- MQTT CLIENT -----------
client = mqtt.Client(protocol=mqtt.MQTTv5)

def setup_mqtt():
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")
        exit(1)

# ----------- CALLBACKS -----------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Successfully connected to MQTT broker.")
        # Subscribe to relevant topics
        client.subscribe(Topics.PIR_MOTION_DETECTED.value)
        client.subscribe(Topics.PIR_MOTION_ENDED.value)
        client.subscribe(Topics.PIR_HEARTBEAT.value)
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")

def on_message(client, userdata, msg):
    logger.info(f"Message received on topic '{msg.topic}': {msg.payload.decode()}")
    if msg.topic == Topics.PIR_MOTION_DETECTED.value:
        handle_motion_detected(msg.payload.decode())
    elif msg.topic == Topics.PIR_MOTION_ENDED.value:
        handle_motion_ended(msg.payload.decode())
    elif msg.topic == Topics.PIR_HEARTBEAT.value:
        handle_heartbeat(msg.payload.decode())

# ----------- EVENT HANDLERS -----------
def handle_motion_detected(payload):
    logger.info("Handling motion detected event.")
    try:
        data = parse_payload(payload)
        logger.info(f"Motion detected at {data['timestamp']}. Triggering alarm.")
        # Example: Publish an alarm event
        alarm_payload = create_payload(source="controller", event="ALARM_TRIGGERED", data={"reason": "Motion detected"})
        publish_payload(client, Topics.PICTURE_TAKEN.value, alarm_payload)
    except Exception as e:
        logger.error(f"Failed to handle motion detected event: {e}")

def handle_motion_ended(payload):
    logger.info("Handling motion ended event.")
    try:
        data = parse_payload(payload)
        logger.info(f"Motion ended at {data['timestamp']}.")
        # Example: Publish an event to indicate motion has stopped
        stop_payload = create_payload(source="controller", event="ALARM_CLEARED", data={"reason": "Motion ended"})
        publish_payload(client, Topics.PICTURE_TAKEN.value, stop_payload)
    except Exception as e:
        logger.error(f"Failed to handle motion ended event: {e}")

def handle_heartbeat(payload):
    logger.info("Handling PIR sensor heartbeat.")
    try:
        data = parse_payload(payload)
        logger.info(f"Heartbeat received from PIR sensor at {data['timestamp']}.")
    except Exception as e:
        logger.error(f"Failed to handle heartbeat: {e}")

# ----------- UTILITY FUNCTIONS -----------
def parse_payload(payload):
    """
    Parses the JSON payload and returns it as a dictionary.
    """
    import json
    try:
        return json.loads(payload)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse payload: {e}")
        raise

# ----------- MAIN LOOP -----------
def main():
    setup_mqtt()
    client.on_connect = on_connect
    client.on_message = on_message

    logger.info("Starting controller...")
    client.loop_forever()

if __name__ == "__main__":
    main()
