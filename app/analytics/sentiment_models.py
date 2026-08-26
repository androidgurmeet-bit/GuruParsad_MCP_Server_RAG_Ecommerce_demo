from enum import Enum

from pydantic import BaseModel, Field


class SentimentType(str, Enum):
    """The sentiments the analyzer may return.

    str-valued so it serializes straight to a plain string alongside the
    conversation records.
    """

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class SentimentResult(BaseModel):
    sentiment: SentimentType
    confidence: float = Field(ge=0.0, le=1.0)


# What we fall back to when the model is unreachable or returns something
# unusable — an unscored message should not fail the request.
UNKNOWN_SENTIMENT = SentimentResult(sentiment=SentimentType.NEUTRAL, confidence=0.0)
