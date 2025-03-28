import logging

import paho.mqtt.client as mqtt
from mqtt_topics import Topics  # Import Topics enum
from mqtt_payload import create_payload, publish_payload  # Import helper functions

# Configure logging
logging.basicConfig(
    filename="mqtt_messages.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT broker successfully")
        client.subscribe(Topics.ALL_TOPICS.value)  # Subscribe to all topics
    else:
        logging.error(f"Failed to connect, return code {rc}")

# Callback when the client disconnects from the broker
def on_disconnect(client, userdata, rc):
    if rc != 0:
        logging.warning("Unexpected disconnection. Attempting to reconnect...")
        try:
            client.reconnect()
        except Exception as e:
            logging.error(f"Reconnection failed: {e}")

# Callback when a message is received
def on_message(client, userdata, msg):
    logging.info(f"Topic: {msg.topic}, Message: {msg.payload.decode('utf-8')}")
    if msg.topic == Topics.PIR_MOTION_DETECTED.value:  # Example usage
        logging.info("Motion detected event received.")
        response_payload = create_payload(source="intercept-all-mqtt", event="MOTION_DETECTED_ACK")
        publish_payload(client, Topics.PIR_MOTION_DETECTED.value, response_payload)  # Use standardized payload

# MQTT client setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Connect to the MQTT broker
broker_address = "localhost"  # Replace with your broker address
broker_port = 1883  # Default MQTT port
client.connect(broker_address, broker_port, 60)

# Start the loop to process network traffic and callbacks
client.loop_forever()