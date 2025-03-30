import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import RPi.GPIO as GPIO
import time
import logging
from mqtt_topics import Topics  # Import Topics enum
from mqtt_client import get_mqtt_client  # Import the singleton MQTT client
from mqtt_payload import create_payload, publish_payload  # Import helper functions

# ----------- KONFIGURATION -----------
PIR_PIN = 17  # GPIO pin for the PIR sensor (physical pin 11)
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "pir_sensor.log")

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
client = get_mqtt_client()
if client is None:
    logger.error("Failed to initialize MQTT client. Exiting...")
    sys.exit(1)

# ----------- PIR SENSOR SETUP -----------
def setup_pir_sensor():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIR_PIN, GPIO.IN)
    logger.info("PIR sensor initialized.")

# ----------- CALLBACKS -----------
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("Successfully connected to MQTT broker.")
        # Subscribe to ARM and DISARM topics
        client.subscribe([
            (Topics.PIR_ARM.value, 0),
            (Topics.PIR_DISARM.value, 0)
        ])
        logger.info(f"Subscribed to topics: {Topics.PIR_ARM.value}, {Topics.PIR_DISARM.value}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")

def on_message(client, userdata, msg):
    logger.info(f"Message received on topic '{msg.topic}': {msg.payload.decode()}")
    if msg.topic == Topics.PIR_ARM.value:
        arm_sensor()
    elif msg.topic == Topics.PIR_DISARM.value:
        disarm_sensor()

# ----------- SENSOR CONTROL -----------
monitoring = True  # Set monitoring to True by default

def arm_sensor():
    global monitoring
    monitoring = True
    logger.info("PIR sensor monitoring armed.")

def disarm_sensor():
    global monitoring
    monitoring = False
    logger.info("PIR sensor monitoring disarmed.")

# ----------- SENSOR MONITORING -----------
def monitor_pir_sensor():
    global monitoring
    logger.info("Starting PIR sensor monitoring...")
    last_state = False  # Track the last state of the PIR sensor (False = no motion, True = motion)

    try:
        while True:
            if monitoring:
                current_state = GPIO.input(PIR_PIN)  # Read the current state of the PIR sensor
                # logger.info(f"Current state: {current_state}, Last state: {last_state}")
                if current_state and not last_state:  # Motion detected (state changed from OFF to ON)
                    logger.info("Motion detected!")
                    payload = create_payload(source="pir-sensor", event="MOTION_DETECTED")
                    publish_payload(Topics.PIR_MOTION_DETECTED.value, payload)
                last_state = current_state  # Update the last state
            time.sleep(0.25)  # Polling interval
    except KeyboardInterrupt:
        logger.info("Stopping PIR sensor monitoring...")
    finally:
        GPIO.cleanup()
        client.disconnect()

# ----------- MAIN LOOP -----------
def main():
    setup_pir_sensor()
    client.on_connect = on_connect
    client.on_message = on_message

    logger.info("Starting PIR sensor service...")
    client.loop_start()
    monitor_pir_sensor()

if __name__ == "__main__":
    main()
