from dataclasses import dataclass

import httpx

from app.config.settings import get_settings


@dataclass
class StockQuote:
    symbol: str
    price: float
    change: float
    change_percent: str
    volume: int
    latest_trading_day: str


class MarketDataError(Exception):
    """Raised when market data cannot be retrieved."""


class AlphaVantageMarketData:
    """Market data client using Alpha Vantage."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self):
        settings = get_settings()

        if not settings.alpha_vantage_api_key:
            raise MarketDataError(
                "ALPHA_VANTAGE_API_KEY is not configured."
            )

        self.api_key = settings.alpha_vantage_api_key

    async def get_quote(self, symbol: str) -> StockQuote:
        """Get the latest available quote for a stock."""

        symbol = symbol.strip().upper()

        if not symbol:
            raise MarketDataError(
                "Stock symbol cannot be empty."
            )

        params = {
            "function": "GLOBAL_QUOTE",
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
            raise MarketDataError(
                f"Unable to connect to Alpha Vantage: {exc}"
            ) from exc

        # Alpha Vantage may return an information/error message
        # instead of quote data.
        if "Information" in data:
            raise MarketDataError(
                data["Information"]
            )

        if "Note" in data:
            raise MarketDataError(
                data["Note"]
            )

        quote = data.get("Global Quote")

        if not quote:
            raise MarketDataError(
                f"No market data found for symbol '{symbol}'."
            )

        try:
            return StockQuote(
                symbol=quote["01. symbol"],
                price=float(quote["05. price"]),
                change=float(quote["09. change"]),
                change_percent=quote["10. change percent"],
                volume=int(quote["06. volume"]),
                latest_trading_day=quote["07. latest trading day"],
            )

        except (KeyError, ValueError) as exc:
            raise MarketDataError(
                "Alpha Vantage returned an unexpected quote format."
            ) from exc


async def get_stock_quote(symbol: str) -> StockQuote:
    """Convenience function for retrieving a stock quote."""

    provider = AlphaVantageMarketData()

    return await provider.get_quote(symbol)