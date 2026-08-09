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
    Extract a stock ticker or known company symbol
    from the user's message.
    """

    # ---------------------------------------------------------
    # Explicit ticker format:
    # Examples:
    # $AAPL
    # $NVDA
    # $IBM
    # ---------------------------------------------------------

    ticker_match = re.search(
        r"\$([A-Za-z]{1,5})\b",
        message,
    )

    if ticker_match:
        return ticker_match.group(1).upper()

    # ---------------------------------------------------------
    # Common company -> ticker mappings.
    #
    # This is intentionally limited for the MVP.
    # We can replace this later with a proper symbol
    # lookup service.
    # ---------------------------------------------------------

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
        "paypal": "PYPL",
        "uber": "UBER",
        "spotify": "SPOT",
        "shopify": "SHOP",
        "coca cola": "KO",
        "coca-cola": "KO",
        "pepsico": "PEP",
        "walmart": "WMT",
        "jpmorgan": "JPM",
        "jp morgan": "JPM",
        "goldman sachs": "GS",
        "visa": "V",
        "mastercard": "MA",
        "berkshire hathaway": "BRK.B",
    }

    text = message.lower()

    for company, symbol in company_symbols.items():
        if company in text:
            return symbol

    return None


def create_plan(message: str) -> Plan:
    """
    Create a deterministic execution plan for the user's request.

    The planner determines:
    - user's intent
    - whether live data is required
    - whether a tool is required
    - stock/company symbol when identifiable
    """

    text = message.lower().strip()

    # =========================================================
    # DOCUMENT ANALYSIS
    # =========================================================

    document_keywords = [
        "document",
        "pdf",
        "annual report",
        "quarterly report",
        "financial statement",
        "filing",
        "10-k",
        "10-q",
        "document analysis",
    ]

    if any(keyword in text for keyword in document_keywords):
        return Plan(
            intent=Intent.DOCUMENT_ANALYSIS,
            requires_document=True,
            requires_tool=True,
        )

    # =========================================================
    # MARKET DATA
    # =========================================================

    market_keywords = [
        "stock price",
        "share price",
        "market price",
        "stock",
        "shares",
        "market cap",
        "pe ratio",
        "p/e",
        "trading at",
        "stock quote",
        "share quote",
        "current price",
        "current stock",
        "price of",
    ]

    if any(keyword in text for keyword in market_keywords):
        return Plan(
            intent=Intent.MARKET_DATA,
            requires_live_data=True,
            requires_tool=True,
            symbol=extract_symbol(message),
        )

    # =========================================================
    # NEWS
    # =========================================================

    news_keywords = [
        "news",
        "latest news",
        "recent news",
        "today",
        "what happened",
        "announcement",
        "breaking news",
    ]

    if any(keyword in text for keyword in news_keywords):
        return Plan(
            intent=Intent.NEWS,
            requires_live_data=True,
            requires_tool=True,
            symbol=extract_symbol(message),
        )

    # =========================================================
    # COMPANY RESEARCH
    # =========================================================

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
        "business model",
        "industry",
        "sector",
        "headquarters",
        "management",
    ]

    # ---------------------------------------------------------
    # Company-specific financial questions.
    #
    # Examples:
    # "What is Apple's revenue?"
    # "What is IBM's profit?"
    # "What is NVIDIA's market cap?"
    # ---------------------------------------------------------

    financial_keywords = [
        "revenue",
        "profit",
        "earnings",
        "market cap",
        "market capitalization",
        "p/e",
        "pe ratio",
        "dividend",
        "profit margin",
        "financial performance",
    ]

    symbol = extract_symbol(message)

    if symbol and any(
        keyword in text
        for keyword in financial_keywords
    ):
        return Plan(
            intent=Intent.COMPANY_RESEARCH,
            requires_live_data=True,
            requires_tool=True,
            symbol=symbol,
        )

    # ---------------------------------------------------------
    # General company questions.
    #
    # Example:
    # "Tell me about IBM"
    # "Tell me about NVIDIA"
    # ---------------------------------------------------------

    if any(keyword in text for keyword in company_keywords):
        return Plan(
            intent=Intent.COMPANY_RESEARCH,
            requires_live_data=True,
            requires_tool=True,
            symbol=symbol,
        )

    # ---------------------------------------------------------
    # If a known company is mentioned by itself, treat it as
    # company research.
    #
    # Example:
    # "Tell me about Apple"
    # "NVIDIA"
    # ---------------------------------------------------------

    if symbol:
        return Plan(
            intent=Intent.COMPANY_RESEARCH,
            requires_live_data=True,
            requires_tool=True,
            symbol=symbol,
        )

    # =========================================================
    # GENERAL
    # =========================================================

    return Plan(
        intent=Intent.GENERAL
    )