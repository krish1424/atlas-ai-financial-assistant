from dataclasses import dataclass
from datetime import datetime

import httpx

from app.config.settings import get_settings


@dataclass
class NewsArticle:
    title: str
    summary: str
    url: str
    source: str
    published_at: datetime | None
    sentiment: str | None
    sentiment_score: float | None


class NewsDataError(Exception):
    """Raised when financial news cannot be retrieved."""


class AlphaVantageNewsData:
    """Financial news client using Alpha Vantage."""

    BASE_URL = "https://www.alphavantage.co/query"

    COMPANY_ALIASES = {
        "IBM": [
            "ibm",
            "international business machines",
        ],
        "AAPL": [
            "aapl",
            "apple",
            "apple inc",
            "apple incorporated",
        ],
        "MSFT": [
            "msft",
            "microsoft",
            "microsoft corporation",
        ],
        "GOOGL": [
            "googl",
            "google",
            "alphabet",
            "alphabet inc",
        ],
        "AMZN": [
            "amzn",
            "amazon",
            "amazon.com",
            "amazon inc",
        ],
        "NVDA": [
            "nvda",
            "nvidia",
            "nvidia corporation",
        ],
        "TSLA": [
            "tsla",
            "tesla",
            "tesla inc",
        ],
        "META": [
            "meta",
            "meta platforms",
            "facebook",
        ],
        "NFLX": [
            "nflx",
            "netflix",
            "netflix inc",
        ],
        "INTC": [
            "intc",
            "intel",
            "intel corporation",
        ],
        "AMD": [
            "amd",
            "advanced micro devices",
        ],
        "ORCL": [
            "orcl",
            "oracle",
            "oracle corporation",
        ],
        "ADBE": [
            "adbe",
            "adobe",
            "adobe inc",
        ],
        "CRM": [
            "crm",
            "salesforce",
            "salesforce.com",
        ],
        "PYPL": [
            "pypl",
            "paypal",
            "paypal holdings",
        ],
        "UBER": [
            "uber",
            "uber technologies",
        ],
        "SPOT": [
            "spot",
            "spotify",
            "spotify technology",
        ],
        "SHOP": [
            "shop",
            "shopify",
            "shopify inc",
        ],
        "KO": [
            "ko",
            "coca cola",
            "coca-cola",
            "coca-cola company",
        ],
        "PEP": [
            "pep",
            "pepsico",
            "pepsico inc",
        ],
        "JPM": [
            "jpm",
            "jpmorgan",
            "jp morgan",
            "jpmorgan chase",
        ],
        "GS": [
            "gs",
            "goldman sachs",
            "goldman sachs group",
        ],
        "V": [
            "visa",
            "visa inc",
        ],
        "MA": [
            "mastercard",
            "mastercard incorporated",
        ],
    }

    def __init__(self):
        settings = get_settings()

        if not settings.alpha_vantage_api_key:
            raise NewsDataError(
                "ALPHA_VANTAGE_API_KEY is not configured."
            )

        self.api_key = settings.alpha_vantage_api_key

    async def get_news(
        self,
        symbol: str | None = None,
        limit: int = 5,
    ) -> list[NewsArticle]:
        """
        Retrieve financial news from Alpha Vantage.

        When a symbol is provided, only articles that explicitly
        mention the requested company/ticker are returned.
        """

        if limit < 1:
            raise NewsDataError(
                "News limit must be greater than zero."
            )

        requested_symbol = None

        if symbol:
            requested_symbol = symbol.strip().upper()

            if not requested_symbol:
                raise NewsDataError(
                    "Company symbol cannot be empty."
                )

        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": self.api_key,
            "sort": "LATEST",
            # Request extra articles because our strict filter
            # may reject unrelated articles.
            "limit": max(limit * 3, 20),
        }

        if requested_symbol:
            params["tickers"] = requested_symbol

        try:
            async with httpx.AsyncClient(
                timeout=15.0
            ) as client:
                response = await client.get(
                    self.BASE_URL,
                    params=params,
                )

                response.raise_for_status()
                data = response.json()

        except httpx.HTTPError as exc:
            raise NewsDataError(
                f"Unable to connect to Alpha Vantage: {exc}"
            ) from exc

        if "Information" in data:
            raise NewsDataError(
                data["Information"]
            )

        if "Note" in data:
            raise NewsDataError(
                data["Note"]
            )

        feed = data.get("feed", [])

        if not feed:
            raise NewsDataError(
                "No financial news was found."
            )

        # Strict company relevance filtering.
        if requested_symbol:
            feed = self._filter_relevant_articles(
                feed=feed,
                symbol=requested_symbol,
            )

            if not feed:
                raise NewsDataError(
                    f"No relevant financial news was found "
                    f"for {requested_symbol}."
                )

        articles: list[NewsArticle] = []

        for item in feed[:limit]:
            published_at = self._parse_published_time(
                item.get("time_published")
            )

            articles.append(
                NewsArticle(
                    title=item.get(
                        "title",
                        "",
                    ),
                    summary=item.get(
                        "summary",
                        "",
                    ),
                    url=item.get(
                        "url",
                        "",
                    ),
                    source=item.get(
                        "source",
                        "",
                    ),
                    published_at=published_at,
                    sentiment=item.get(
                        "overall_sentiment_label"
                    ),
                    sentiment_score=_to_float(
                        item.get(
                            "overall_sentiment_score"
                        )
                    ),
                )
            )

        if not articles:
            raise NewsDataError(
                "No usable financial news articles were found."
            )

        return articles

    @classmethod
    def _filter_relevant_articles(
        cls,
        feed: list[dict],
        symbol: str,
    ) -> list[dict]:
        """
        Strictly filter articles for a company.

        An article is accepted only when the requested ticker
        or one of its known company names appears in the
        article title, summary, or URL.

        We deliberately do NOT rely on Alpha Vantage's
        relevance_score because it can include articles about
        other companies that merely share the same broader
        financial topic.
        """

        aliases = cls.COMPANY_ALIASES.get(
            symbol,
            [symbol.lower()],
        )

        relevant_articles: list[dict] = []

        for item in feed:
            title = str(
                item.get("title", "")
            ).lower()

            summary = str(
                item.get("summary", "")
            ).lower()

            url = str(
                item.get("url", "")
            ).lower()

            searchable_text = (
                f"{title} {summary} {url}"
            )

            if any(
                alias.lower() in searchable_text
                for alias in aliases
            ):
                relevant_articles.append(item)

        return relevant_articles

    @staticmethod
    def _parse_published_time(
        raw_time: str | None,
    ) -> datetime | None:
        """Convert Alpha Vantage timestamp to datetime."""

        if not raw_time:
            return None

        try:
            return datetime.strptime(
                raw_time,
                "%Y%m%dT%H%M%S",
            )

        except ValueError:
            return None


def _to_float(
    value: str | float | int | None,
) -> float | None:
    """Safely convert a value to float."""

    if value is None:
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


async def get_financial_news(
    symbol: str | None = None,
    limit: int = 5,
) -> list[NewsArticle]:
    """
    Convenience function for retrieving financial news.
    """

    provider = AlphaVantageNewsData()

    return await provider.get_news(
        symbol=symbol,
        limit=limit,
    )