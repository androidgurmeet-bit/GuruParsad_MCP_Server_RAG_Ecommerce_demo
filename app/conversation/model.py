from datetime import datetime

from pydantic import BaseModel

from .intent_models import IntentType


class Conversation(BaseModel):
    conversation_id: str
    channel: str
    customer_id: str | None = None
    message: str
    language: str
    intent: IntentType = IntentType.GENERAL_INQUIRY
    confidence: float = 0.0
    timestamp: datetime
