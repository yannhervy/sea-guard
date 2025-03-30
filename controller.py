import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import paho.mqtt.client as mqtt
from mqtt_topics import Topics  # Import Topics enum
from mqtt_payload import create_payload, publish_payload  # Import helper functions

# ----------- KONFIGURATION -----------
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "controller.log")

# Ensure the logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# ----------- LOGGNING -----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
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
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("Successfully connected to MQTT broker.")
        # Subscribe to all topics
        topics = [(topic.value, 0) for topic in Topics]
        client.subscribe(topics)
        logger.info(f"Subscribed to topics: {', '.join([t[0] for t in topics])}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")

def on_message(client, userdata, msg):
    logger.info(f"Message received on topic '{msg.topic}': {msg.payload.decode()}")

# ----------- MAIN LOOP -----------
def main():
    setup_mqtt()
    client.on_connect = on_connect
    client.on_message = on_message

    logger.info("Starting controller...")
    client.loop_forever()

if __name__ == "__main__":
    main()
