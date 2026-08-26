from enum import Enum

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """The intents the classifier may return.

    str-valued so it serializes straight to a plain string in conversation.json.
    """

    PRODUCT_SEARCH = "PRODUCT_SEARCH"
    PRODUCT_COMPARISON = "PRODUCT_COMPARISON"
    ORDER_TRACKING = "ORDER_TRACKING"
    POLICY_INQUIRY = "POLICY_INQUIRY"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    RETURN_PROCESS = "RETURN_PROCESS"
    PAYMENT_ISSUE = "PAYMENT_ISSUE"
    SHIPPING_QUESTION = "SHIPPING_QUESTION"
    PROMOTION_INQUIRY = "PROMOTION_INQUIRY"
    GENERAL_INQUIRY = "GENERAL_INQUIRY"


class IntentResult(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)


# What we fall back to when the model is unreachable or returns something
# unusable — an unclassified message should not fail the request.
UNKNOWN_INTENT = IntentResult(intent=IntentType.GENERAL_INQUIRY, confidence=0.0)
