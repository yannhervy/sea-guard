import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import asyncio
from mqtt_client import get_mqtt_client
from mqtt_topics import Topics
from mqtt_payload import create_payload, publish_payload
from datetime import datetime

logging.basicConfig(level=logging.INFO)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("bot_publisher: Connected to MQTT broker.")
        client.subscribe(Topics.GET_LATEST_PICTURES.value)
        logging.info(f"bot_publisher: Subscribed to {Topics.GET_LATEST_PICTURES.value}")
    else:
        logging.error(f"bot_publisher: Connection failed with rc={rc}")

def on_message(client, userdata, msg):
    """
    Handles incoming requests on GET_LATEST_PICTURES_N.
    For a real setup, fetch the pictures and publish them.
    """
    logging.info(f"bot_publisher: Received message on '{msg.topic}': {msg.payload.decode()}")
    if msg.topic == Topics.GET_LATEST_PICTURES.value:
        # Parse the incoming payload and determine how many images are requested
        # Then publish them or send them somewhere, e.g.:
        try:
            # Example: Just log or re-publish a dummy response
            payload = create_payload(
                source="bot_publisher",
                event="SEND_LATEST_PICTURES",
                data={"info": "Dummy pictures published."}
            )
            publish_payload(Topics.SEND_LATEST_PICTURES.value, payload)
            logging.info("bot_publisher: Published dummy pictures to SEND_LATEST_PICTURES.")
        except Exception as e:
            logging.error(f"bot_publisher: Failed to process request: {e}")

def main():
    client = get_mqtt_client(
        subscriptions=[Topics.GET_LATEST_PICTURES.value],
        client_id="bot_publisher"
    )
    if client is None:
        logging.error("bot_publisher: MQTT client is not available. Exiting.")
        return

    client.on_connect = on_connect
    client.on_message = on_message

    logging.info("bot_publisher: Starting MQTT event loop.")
    client.loop_forever()

if __name__ == "__main__":
    main()
