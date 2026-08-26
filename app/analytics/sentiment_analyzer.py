from langchain_ollama import ChatOllama

from .sentiment_models import SentimentResult


class SentimentAnalyzer:

    def __init__(self):

        self.llm = ChatOllama(
            model="qwen3:1.7b",
            temperature=0
        )

    async def analyze(
        self,
        message: str
    ) -> SentimentResult:

        prompt = f"""
You are a sentiment analysis system for an ecommerce application.

Analyze the customer's message.

Classify it into exactly ONE of:

POSITIVE
NEGATIVE
NEUTRAL

Return ONLY valid JSON.

Format:

{{
    "sentiment": "POSITIVE",
    "confidence": 0.95
}}

Customer message:
{message}
"""

        response = await self.llm.ainvoke(prompt)

        return SentimentResult.model_validate_json(
            response.content
        )