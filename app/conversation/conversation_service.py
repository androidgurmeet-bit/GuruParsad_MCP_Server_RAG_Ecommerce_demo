import uuid
from datetime import datetime, timezone

from .intent_detector import IntentDetector
from .intent_models import UNKNOWN_INTENT, IntentResult
from .model import Conversation
from .parser import language_from_transcript, message_from_transcript
from .storage import save_conversation


class ConversationService:
    """Builds and persists the Conversation record for one inbound message."""

    def __init__(self, intent_detector: IntentDetector | None = None):
        self.intent_detector = intent_detector or IntentDetector()

    def create(
        self,
        message: str,
        language: str,
        channel: str = "voice",
        customer_id: str | None = None,
        intent: IntentResult = UNKNOWN_INTENT,
    ) -> Conversation:
        return Conversation(
            conversation_id=str(uuid.uuid4()),
            channel=channel,
            customer_id=customer_id,
            message=message,
            language=language,
            intent=intent.intent,
            confidence=intent.confidence,
            # UTC so records from different machines stay comparable.
            timestamp=datetime.now(timezone.utc),
        )

    async def create_from_transcript(
        self,
        call_id: str,
        transcript: dict,
        customer_id: str | None = None,
    ) -> Conversation:
        """Voice path: transcript dict → intent → Conversation → conversation.json."""
        message = message_from_transcript(transcript)
        intent = await self.intent_detector.detect(message)

        conversation = self.create(
            message=message,
            language=language_from_transcript(transcript),
            channel="voice",
            customer_id=customer_id,
            intent=intent,
        )
        save_conversation(call_id, conversation)
        return conversation
