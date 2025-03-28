import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import RPi.GPIO as GPIO
import time
import logging
import paho.mqtt.client as mqtt
from datetime import datetime
from mqtt_topics import Topics  # Import Topics enum
from mqtt_payload import create_payload, publish_payload  # Import helper functions

# ----------- KONFIGURATION -----------
PIR_PIN = 17  # GPIO pin for the PIR sensor
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_MOTION_DETECTED = Topics.PIR_MOTION_DETECTED.value
MQTT_TOPIC_MOTION_ENDED = Topics.PIR_MOTION_ENDED.value
MQTT_TOPIC_HEARTBEAT = Topics.PIR_HEARTBEAT.value
HEARTBEAT_INTERVAL = 60  # Heartbeat interval in seconds

# ----------- LOGGNING -----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pir_sensor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------- MQTT CLIENT -----------
client = mqtt.Client(protocol=mqtt.MQTTv5)  # Explicitly specify MQTTv5 protocol

def setup_mqtt():
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        logger.info(f"Ansluten till MQTT-broker på {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        logger.error(f"Misslyckades att ansluta till MQTT-broker: {e}")
        exit(1)

# ----------- PIR SENSOR -----------
def setup_pir_sensor():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIR_PIN, GPIO.IN)

def publish_motion_event(event_type):
    topic = MQTT_TOPIC_MOTION_DETECTED if event_type == "MOTION_DETECTED" else MQTT_TOPIC_MOTION_ENDED
    payload = create_payload(source="pir-sensor", event=event_type)
    publish_payload(client, topic, payload)  # Use standardized payload
    logger.info(f"Published {event_type} to MQTT.")

def monitor_pir_sensor():
    logger.info("Startar PIR-sensorövervakning...")
    motion_detected = False
    last_heartbeat = time.time()

    try:
        while True:
            current_time = time.time()

            # Send heartbeat
            if current_time - last_heartbeat >= HEARTBEAT_INTERVAL:
                payload = create_payload(source="pir-sensor", event="HEARTBEAT")
                publish_payload(client, MQTT_TOPIC_HEARTBEAT, payload)  # Use standardized payload
                logger.info("Skickade heartbeat.")
                last_heartbeat = current_time

            # Check for motion
            if GPIO.input(PIR_PIN):
                if not motion_detected:
                    logger.info("Rörelse upptäckt!")
                    publish_motion_event("MOTION_DETECTED")
                    motion_detected = True
            else:
                if motion_detected:
                    logger.info("Rörelse avslutad.")
                    publish_motion_event("MOTION_ENDED")
                    motion_detected = False

            time.sleep(0.1)
    except KeyboardInterrupt:
        logger.info("Avslutar PIR-sensorövervakning...")
    finally:
        GPIO.cleanup()
        client.disconnect()
