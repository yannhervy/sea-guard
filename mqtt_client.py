import logging
import time
import paho.mqtt.client as mqtt
from mqtt_topics import Topics  # Import Topics enum

logger = logging.getLogger(__name__)

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

_client = None

def on_connect(client, userdata, flags, rc):
    """
    Callback for when the client connects to the broker.
    Re-subscribes to all necessary topics.
    """
    if rc == 0:
        logger.info("MQTT: Connected to broker successfully.")
        # Re-subscribe to topics
        subscriptions = userdata.get("subscriptions", [])
        for topic in subscriptions:
            client.subscribe(topic)
            logger.info(f"MQTT: Subscribed to topic: {topic}")
    else:
        logger.error(f"MQTT: Failed to connect to broker, return code {rc}")

def on_disconnect(client, userdata, rc):
    """
    Callback for when the client disconnects from the broker.
    Attempts to reconnect.
    """
    if rc != 0:
        logger.warning("MQTT: Unexpected disconnection. Attempting to reconnect...")
        while True:
            try:
                client.reconnect()
                logger.info("MQTT: Reconnected to broker.")
                break
            except Exception as e:
                logger.error(f"MQTT: Reconnection failed: {e}. Retrying in 5 seconds...")
                time.sleep(5)

def on_message(client, userdata, msg):
    """
    Callback for when a message is received on a subscribed topic.
    Logs the topic and the message payload.
    """
    logger.info(f"MQTT: Message received on topic '{msg.topic}': {msg.payload.decode()}")

def get_mqtt_client(subscriptions=None):
    """
    Returns a singleton MQTT client instance.
    Ensures the client is connected to the broker and sets up callbacks.
    Resubscribes to the provided list of topics after reconnecting.
    """
    global _client
    if _client is None:
        _client = mqtt.Client(userdata={"subscriptions": subscriptions or []})
        _client.on_connect = on_connect
        _client.on_disconnect = on_disconnect
        _client.on_message = on_message
        try:
            _client.connect(MQTT_BROKER, MQTT_PORT, 60)
            logger.info(f"MQTT: Connected to broker at {MQTT_BROKER}:{MQTT_PORT}")
        except Exception as e:
            logger.error(f"MQTT: Failed to connect to broker: {e}")
            _client = None
    else:
        if not _client.is_connected():
            try:
                logger.info("MQTT: Client is not connected. Attempting to reconnect...")
                _client.reconnect()
                logger.info("MQTT: Reconnected to broker.")
                # Resubscribe to topics after reconnecting
                for topic in _client._userdata.get("subscriptions", []):
                    _client.subscribe(topic)
                    logger.info(f"MQTT: Resubscribed to topic: {topic}")
            except Exception as e:
                logger.error(f"MQTT: Failed to reconnect to broker: {e}")
                _client = None
    return _client
