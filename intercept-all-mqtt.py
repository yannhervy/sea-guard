import logging

import paho.mqtt.client as mqtt

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
        client.subscribe("#")  # Subscribe to all topics
    else:
        logging.error(f"Failed to connect, return code {rc}")

# Callback when a message is received
def on_message(client, userdata, msg):
    logging.info(f"Topic: {msg.topic}, Message: {msg.payload.decode('utf-8')}")

# MQTT client setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
broker_address = "localhost"  # Replace with your broker address
broker_port = 1883  # Default MQTT port
client.connect(broker_address, broker_port, 60)

# Start the loop to process network traffic and callbacks
client.loop_forever()