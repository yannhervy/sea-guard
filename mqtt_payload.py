import logging
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import json
import paho.mqtt.client as mqtt

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


def publish_payload(client, topic: str, payload: MQTTPayload):
    """
    Publishes a payload to a given MQTT topic.
    Checks the connection status of the client before publishing.
    """
    if not client.is_connected():
        logger.error(f"MQTT client is not connected. Unable to publish to topic '{topic}'.")
        try:
            logger.info("Attempting to reconnect MQTT client...")
            client.reconnect()
            logger.info("Reconnected successfully.")
        except Exception as e:
            logger.error(f"Failed to reconnect MQTT client: {e}")
            return

    try:
        client.publish(topic, payload.json())
        logger.info(f"Published payload to topic '{topic}': {payload.json()}")
    except Exception as e:
        logger.error(f"Failed to publish payload to topic '{topic}': {e}")
