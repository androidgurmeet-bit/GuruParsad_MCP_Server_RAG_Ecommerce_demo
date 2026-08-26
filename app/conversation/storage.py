import json
from pathlib import Path

from .model import Conversation

CONVERSATIONS_DIR = Path(__file__).resolve().parents[2] / "conversations"


def save_conversation(call_id: str, conversation: Conversation) -> Path:
    """Write conversations/<call_id>.json and return its path.

    Keyed by call_id so the record points back at transcripts/<call_id>/.
    """
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)

    file = CONVERSATIONS_DIR / f"{call_id}.json"
    with file.open("w", encoding="utf-8") as f:
        # mode="json" so datetime becomes an ISO string json.dump can write.
        json.dump(
            conversation.model_dump(mode="json"), f, indent=4, ensure_ascii=False
        )

    return file
