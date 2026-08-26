import json
import logging
import re

from langchain_ollama import ChatOllama
from pydantic import ValidationError

from .intent_models import UNKNOWN_INTENT, IntentResult, IntentType

logger = logging.getLogger(__name__)

INTENT_MODEL = "qwen3:1.7b"

# qwen3 is a reasoning model: it emits a <think> block before the answer, and
# usually fences the JSON. Strip both before looking for the object.
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)
_JSON_OBJECT = re.compile(r"\{[^{}]*\}", re.DOTALL)

_INTENT_NAMES = ", ".join(f'"{intent.value}"' for intent in IntentType)

PROMPT_TEMPLATE = f"""You are an intent classifier for an ecommerce application.
Classify the customer's message into exactly one of these intents:

{_INTENT_NAMES}

Customer message:
{{message}}

Return only JSON in this format, with no explanation:
{{{{"intent": "PRODUCT_SEARCH", "confidence": 0.95}}}}
"""


def parse_intent_response(content: str) -> IntentResult:
    """Pull an IntentResult out of raw model output.

    Falls back to UNKNOWN_INTENT rather than raising — a misclassified message
    is recoverable downstream, a 500 on the transcribe endpoint is not.
    """
    cleaned = _THINK_BLOCK.sub("", content or "")

    match = _JSON_OBJECT.search(cleaned)
    if not match:
        logger.warning("intent: no JSON object in model output: %r", content[:200])
        return UNKNOWN_INTENT

    try:
        payload = json.loads(match.group())
    except json.JSONDecodeError:
        logger.warning("intent: unparseable JSON: %r", match.group()[:200])
        return UNKNOWN_INTENT

    # Clamp rather than reject: models routinely return 95 instead of 0.95,
    # and the intent itself is still worth keeping when they do.
    confidence = payload.get("confidence")
    if isinstance(confidence, (int, float)):
        payload["confidence"] = min(max(float(confidence), 0.0), 1.0)
    else:
        payload["confidence"] = 0.0

    try:
        return IntentResult.model_validate(payload)
    except ValidationError:
        # Usually an intent name outside the enum.
        logger.warning("intent: unrecognised payload: %r", payload)
        return UNKNOWN_INTENT


class IntentDetector:
    def __init__(self, model: str = INTENT_MODEL):
        self.llm = ChatOllama(
            model=model,
            temperature=0,
        )

    async def detect(self, message: str) -> IntentResult:
        if not message.strip():
            return UNKNOWN_INTENT

        try:
            response = await self.llm.ainvoke(PROMPT_TEMPLATE.format(message=message))
        except Exception:
            # Ollama down or model not pulled — classify as unknown and move on.
            logger.exception("intent: model call failed")
            return UNKNOWN_INTENT

        raw = str(response.content)
        result = parse_intent_response(raw)

        # Debug: print goes to the uvicorn console directly. logger.info would be
        # swallowed — uvicorn only configures its own loggers, so app-level INFO
        # never reaches a handler.
        print(f"[intent] message : {message!r}")
        print(f"[intent] raw     : {raw!r}")
        print(f"[intent] parsed  : {result!r}")

        return result
