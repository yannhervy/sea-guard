import logging
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import json
from mqtt_client import get_mqtt_client  # Import the singleton MQTT client

logger = logging.getLogger(__name__)

class MQTTPayload(BaseModel):
    source: str
    event: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        extra = "allow"

def create_payload(source: str, event: str, data: Optional[Dict[str, Any]] = None) -> MQTTPayload:
    return MQTTPayload(
        source=source,
        event=event,
        data=data or {}
    )
def publish_payload_with_client(client, topic: str, payload: MQTTPayload):
    logger.debug(f"BEGIN publish_payload_with_client: '{topic}': {payload.json()}")
    if client is None:
        logger.error(f"MQTT client is not available. Unable to publish to topic '{topic}'.")
        return

    try:
        if not client.is_connected():
            logger.info("MQTT client is not connected. Attempting to reconnect...")
            client.reconnect()
            logger.info("Reconnected to MQTT broker.")
        client.publish(topic, payload.json())
        logger.info(f"Published payload to topic '{topic}': {payload.json()}")
    except Exception as e:
        logger.error(f"Failed to publish payload to topic '{topic}': {e}")


def publish_payload(topic: str, payload: MQTTPayload):
    logger.setLevel(logging.DEBUG)  # Set the log level to DEBUG for more visibility
    logger.debug(f"BEGIN publish_payload: '{topic}': {payload.json()}")
    client = get_mqtt_client()
    publish_payload_with_client(client, topic, payload)
    logger.debug(f"END publish_payload: '{topic}': {payload.json()}")
    