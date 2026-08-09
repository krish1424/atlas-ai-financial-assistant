from dataclasses import dataclass

import httpx

from app.config.settings import get_settings


@dataclass
class CompanyOverview:
    symbol: str
    name: str
    description: str
    exchange: str
    currency: str
    country: str
    sector: str
    industry: str
    market_cap: float | None
    revenue_ttm: float | None
    profit_margin: float | None
    pe_ratio: float | None
    dividend_yield: float | None


class CompanyDataError(Exception):
    """Raised when company data cannot be retrieved."""


class AlphaVantageCompanyData:
    """Company fundamentals client using Alpha Vantage."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self):
        settings = get_settings()

        if not settings.alpha_vantage_api_key:
            raise CompanyDataError(
                "ALPHA_VANTAGE_API_KEY is not configured."
            )

        self.api_key = settings.alpha_vantage_api_key

    @staticmethod
    def _to_float(value: str | None) -> float | None:
        if not value or value in {"None", "-", "N/A"}:
            return None

        try:
            return float(value)
        except ValueError:
            return None

    async def get_company_overview(
        self,
        symbol: str,
    ) -> CompanyOverview:

        symbol = symbol.strip().upper()

        if not symbol:
            raise CompanyDataError(
                "Company symbol cannot be empty."
            )

        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    params=params,
                )

                response.raise_for_status()
                data = response.json()

        except httpx.HTTPError as exc:
            raise CompanyDataError(
                f"Unable to connect to Alpha Vantage: {exc}"
            ) from exc

        if "Information" in data:
            raise CompanyDataError(
                data["Information"]
            )

        if "Note" in data:
            raise CompanyDataError(
                data["Note"]
            )

        if not data or not data.get("Symbol"):
            raise CompanyDataError(
                f"No company information found for '{symbol}'."
            )

        return CompanyOverview(
            symbol=data.get("Symbol", symbol),
            name=data.get("Name", ""),
            description=data.get("Description", ""),
            exchange=data.get("Exchange", ""),
            currency=data.get("Currency", ""),
            country=data.get("Country", ""),
            sector=data.get("Sector", ""),
            industry=data.get("Industry", ""),
            market_cap=self._to_float(
                data.get("MarketCapitalization")
            ),
            revenue_ttm=self._to_float(
                data.get("RevenueTTM")
            ),
            profit_margin=self._to_float(
                data.get("ProfitMargin")
            ),
            pe_ratio=self._to_float(
                data.get("PERatio")
            ),
            dividend_yield=self._to_float(
                data.get("DividendYield")
            ),
        )


async def get_company_overview(
    symbol: str,
) -> CompanyOverview:

    provider = AlphaVantageCompanyData()

    return await provider.get_company_overview(symbol)