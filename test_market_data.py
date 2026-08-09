import asyncio

from app.tools.financial.market_data import (
    MarketDataError,
    get_stock_quote,
)


async def main():
    print("Testing market data...")

    try:
        quote = await get_stock_quote("IBM")

        print("Market data retrieved successfully.")
        print(f"Symbol: {quote.symbol}")
        print(f"Price: {quote.price}")
        print(f"Change: {quote.change}")
        print(f"Change %: {quote.change_percent}")
        print(f"Volume: {quote.volume}")
        print(f"Trading day: {quote.latest_trading_day}")

    except MarketDataError as exc:
        print(f"Market data error: {exc}")

    except Exception as exc:
        print(f"Unexpected error: {exc}")


if __name__ == "__main__":
    asyncio.run(main())