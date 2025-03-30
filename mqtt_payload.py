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

def publish_payload(topic: str, payload: MQTTPayload):
    """
    Publishes a payload to a given MQTT topic.
    Uses the singleton MQTT client.
    """
    client = get_mqtt_client()
    if client is None:
        logger.error(f"MQTT client is not available. Unable to publish to topic '{topic}'.")
        return

    try:
        client.publish(topic, payload.json())
        logger.info(f"Published payload to topic '{topic}': {payload.json()}")
    except Exception as e:
        logger.error(f"Failed to publish payload to topic '{topic}': {e}")
