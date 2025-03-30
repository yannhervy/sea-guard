import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import RPi.GPIO as GPIO
import time
import logging
import paho.mqtt.client as mqtt
from mqtt_topics import Topics  # Import Topics enum
from mqtt_payload import create_payload, publish_payload  # Import helper functions

# ----------- KONFIGURATION -----------
PIR_PIN = 17  # GPIO pin for the PIR sensor (physical pin 11)
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_MOTION_DETECTED = Topics.PIR_MOTION_DETECTED.value
MQTT_TOPIC_MOTION_ENDED = Topics.PIR_MOTION_ENDED.value

monitoring = True  # Start monitoring by default

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
client = mqtt.Client(protocol=mqtt.MQTTv5)

def on_message(client, userdata, msg):
    global monitoring
    logger.info(f"Message received on topic '{msg.topic}': {msg.payload.decode()}")
    if msg.topic == Topics.PIR_ARM.value:
        monitoring = True
        logger.info("PIR sensor monitoring armed.")
    elif msg.topic == Topics.PIR_DISARM.value:
        monitoring = False
        logger.info("PIR sensor monitoring disarmed.")
    elif msg.topic == Topics.PIR_MOTION_DETECTED.value:
        logger.info("Motion detected event received.")
    elif msg.topic == Topics.PIR_MOTION_ENDED.value:
        logger.info("Motion ended event received.")
    else:
        logger.warning(f"Unhandled topic: {msg.topic}")

def setup_mqtt():
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        # Subscribe to all relevant topics
        client.subscribe([
            (Topics.PIR_ARM.value, 0),
            (Topics.PIR_DISARM.value, 0),
            (Topics.PIR_MOTION_DETECTED.value, 0),
            (Topics.PIR_MOTION_ENDED.value, 0)
        ])
        client.on_message = on_message
        logger.info(f"Subscribed to topics: {', '.join([t.value for t in Topics])}")
        logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")
        exit(1)

# ----------- PIR SENSOR -----------
def setup_pir_sensor():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIR_PIN, GPIO.IN)

def publish_motion_event(event_type):
    topic = MQTT_TOPIC_MOTION_DETECTED if event_type == "MOTION_DETECTED" else MQTT_TOPIC_MOTION_ENDED
    payload = create_payload(source="pir-sensor", event=event_type)
    publish_payload(topic, payload)
    logger.info(f"Published {event_type} to MQTT.")

def monitor_pir_sensor():
    global monitoring
    logger.info("Starting PIR sensor monitoring...")
    motion_detected = False

    try:
        while True:
            if monitoring:
                # Check for motion
                if GPIO.input(PIR_PIN):
                    if not motion_detected:
                        logger.info("Motion detected!")
                        publish_motion_event("MOTION_DETECTED")
                        motion_detected = True
                else:
                    if motion_detected:
                        logger.info("Motion ended.")
                        publish_motion_event("MOTION_ENDED")
                        motion_detected = False

                time.sleep(0.1)
            else:
                time.sleep(1)  # Sleep while disarmed
    except KeyboardInterrupt:
        logger.info("Stopping PIR sensor monitoring...")
    finally:
        GPIO.cleanup()
        client.disconnect()

if __name__ == "__main__":
    setup_mqtt()
    setup_pir_sensor()
    monitor_pir_sensor()
