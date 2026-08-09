from dataclasses import dataclass
from enum import Enum
import re


class Intent(str, Enum):
    GENERAL = "general"
    COMPANY_RESEARCH = "company_research"
    MARKET_DATA = "market_data"
    NEWS = "news"
    DOCUMENT_ANALYSIS = "document_analysis"
    FINANCIAL_ANALYSIS = "financial_analysis"
    PRODUCTIVITY = "productivity"


@dataclass
class Plan:
    intent: Intent
    requires_live_data: bool = False
    requires_document: bool = False
    requires_tool: bool = False
    symbol: str | None = None


def extract_symbol(message: str) -> str | None:
    """
    Try to extract a stock ticker from a user message.

    This is intentionally conservative. We first support
    explicit ticker formats such as $AAPL or common
    company/ticker references.
    """

    # Match $AAPL, $MSFT, $IBM, etc.
    ticker_match = re.search(
        r"\$([A-Za-z]{1,5})\b",
        message,
    )

    if ticker_match:
        return ticker_match.group(1).upper()

    # Common company → ticker mappings for the first MVP.
    company_symbols = {
        "apple": "AAPL",
        "microsoft": "MSFT",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "amazon": "AMZN",
        "nvidia": "NVDA",
        "tesla": "TSLA",
        "meta": "META",
        "facebook": "META",
        "ibm": "IBM",
        "netflix": "NFLX",
        "intel": "INTC",
        "amd": "AMD",
        "oracle": "ORCL",
        "adobe": "ADBE",
        "salesforce": "CRM",
    }

    text = message.lower()

    for company, symbol in company_symbols.items():
        if company in text:
            return symbol

    return None


def create_plan(message: str) -> Plan:
    """
    Create a deterministic execution plan.

    The planner determines the user's intent and identifies
    whether a live financial tool is required.
    """

    text = message.lower()

    document_keywords = [
        "document",
        "pdf",
        "report",
        "annual report",
        "quarterly report",
        "financial statement",
        "filing",
    ]

    market_keywords = [
        "stock price",
        "share price",
        "market price",
        "price of",
        "stock",
        "shares",
        "market cap",
        "pe ratio",
        "p/e",
        "trading at",
        "quote",
    ]

    news_keywords = [
        "news",
        "latest news",
        "recent news",
        "today",
        "what happened",
        "announcement",
    ]

    company_keywords = [
        "company",
        "business",
        "competitor",
        "ceo",
        "funding",
        "acquisition",
        "merger",
        "earnings",
        "financial performance",
        "how is",
        "performance of",
    ]

    if any(keyword in text for keyword in document_keywords):
        return Plan(
            intent=Intent.DOCUMENT_ANALYSIS,
            requires_document=True,
            requires_tool=True,
        )

    if any(keyword in text for keyword in market_keywords):
        return Plan(
            intent=Intent.MARKET_DATA,
            requires_live_data=True,
            requires_tool=True,
            symbol=extract_symbol(message),
        )

    if any(keyword in text for keyword in news_keywords):
        return Plan(
            intent=Intent.NEWS,
            requires_live_data=True,
            requires_tool=True,
        )

    if any(keyword in text for keyword in company_keywords):
        return Plan(
            intent=Intent.COMPANY_RESEARCH,
            requires_live_data=True,
            requires_tool=True,
        )

    return Plan(
        intent=Intent.GENERAL
    )