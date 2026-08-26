import asyncio

from app.analytics.sentiment_analyzer import SentimentAnalyzer


async def main():

    analyzer = SentimentAnalyzer()

    messages = [

        "I really love this phone. The camera is excellent.",

        "I am very disappointed. The delivery was extremely late.",

        "Show me Samsung phones under 40000.",

    ]

    for message in messages:

        result = await analyzer.analyze(message)

        print()
        print("Message :", message)
        print("Result  :", result)


if __name__ == "__main__":
    asyncio.run(main())