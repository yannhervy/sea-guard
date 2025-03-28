from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import json


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
    try:
        client.publish(topic, payload.json())
    except Exception as e:
        print(f"Failed to publish payload to topic '{topic}': {e}")
