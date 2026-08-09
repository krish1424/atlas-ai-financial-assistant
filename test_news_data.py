import asyncio

from app.tools.financial.news_data import (
    NewsDataError,
    get_financial_news,
)


async def main():
    print("Testing financial news...")

    try:
        articles = await get_financial_news(
            symbol="IBM",
            limit=5,
        )

        print(
            f"Retrieved {len(articles)} articles."
        )

        for index, article in enumerate(
            articles,
            start=1,
        ):
            print("\n" + "=" * 60)
            print(f"Article {index}")
            print(f"Title: {article.title}")
            print(f"Source: {article.source}")
            print(f"Published: {article.published_at}")
            print(f"Sentiment: {article.sentiment}")
            print(
                f"Sentiment score: "
                f"{article.sentiment_score}"
            )
            print(f"URL: {article.url}")
            print(f"Summary: {article.summary}")

    except NewsDataError as exc:
        print(f"News data error: {exc}")

    except Exception as exc:
        print(f"Unexpected error: {exc}")


if __name__ == "__main__":
    asyncio.run(main())