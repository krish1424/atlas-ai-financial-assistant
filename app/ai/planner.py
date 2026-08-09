from dataclasses import dataclass
from enum import Enum


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


def create_plan(message: str) -> Plan:
    """
    Basic deterministic planner.

    We will later replace/extend this with LLM-based intent detection.
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
        "market cap",
        "pe ratio",
        "p/e",
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
        "revenue",
        "profit",
        "competitor",
        "ceo",
        "funding",
        "acquisition",
        "merger",
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

    return Plan(intent=Intent.GENERAL)