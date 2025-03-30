import logging
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

_client = None

def get_mqtt_client():
    """
    Returns a singleton MQTT client instance.
    Ensures the client is connected to the broker.
    """
    global _client
    if _client is None:
        _client = mqtt.Client()
        try:
            _client.connect(MQTT_BROKER, MQTT_PORT, 60)
            logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            _client = None
    return _client
