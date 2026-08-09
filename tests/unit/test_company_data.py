from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools.financial.company_data import (
    AlphaVantageCompanyData,
    CompanyDataError,
)


def create_provider() -> AlphaVantageCompanyData:
    provider = AlphaVantageCompanyData.__new__(
        AlphaVantageCompanyData
    )

    provider.api_key = "test-api-key"

    return provider


def create_mock_response(data: dict) -> MagicMock:
    response = MagicMock()

    response.raise_for_status.return_value = None
    response.json.return_value = data

    return response


def test_to_float_converts_valid_value():
    assert (
        AlphaVantageCompanyData._to_float("123.45")
        == 123.45
    )


def test_to_float_returns_none_for_invalid_value():
    assert (
        AlphaVantageCompanyData._to_float("N/A")
        is None
    )


def test_to_float_returns_none_for_empty_value():
    assert (
        AlphaVantageCompanyData._to_float("")
        is None
    )


@pytest.mark.anyio
async def test_company_overview_parses_response():
    provider = create_provider()

    fake_response = {
        "Symbol": "IBM",
        "Name": "International Business Machines",
        "Description": "Technology company",
        "Exchange": "NYSE",
        "Currency": "USD",
        "Country": "USA",
        "Sector": "TECHNOLOGY",
        "Industry": "COMPUTER SERVICES",
        "MarketCapitalization": "100000000000",
        "RevenueTTM": "60000000000",
        "ProfitMargin": "0.15",
        "PERatio": "22.5",
        "DividendYield": "0.03",
    }

    mock_response = create_mock_response(
        fake_response
    )

    with patch(
        "httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await provider.get_company_overview(
            "IBM"
        )

    assert result.symbol == "IBM"
    assert (
        result.name
        == "International Business Machines"
    )
    assert result.exchange == "NYSE"
    assert result.country == "USA"
    assert result.sector == "TECHNOLOGY"
    assert result.industry == "COMPUTER SERVICES"
    assert result.market_cap == 100000000000.0
    assert result.revenue_ttm == 60000000000.0
    assert result.profit_margin == 0.15
    assert result.pe_ratio == 22.5
    assert result.dividend_yield == 0.03


@pytest.mark.anyio
async def test_company_overview_rejects_empty_symbol():
    provider = create_provider()

    with pytest.raises(
        CompanyDataError,
        match="Company symbol cannot be empty",
    ):
        await provider.get_company_overview("")


@pytest.mark.anyio
async def test_company_overview_handles_api_information_error():
    provider = create_provider()

    fake_response = {
        "Information": "API rate limit reached."
    }

    mock_response = create_mock_response(
        fake_response
    )

    with patch(
        "httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        with pytest.raises(
            CompanyDataError,
            match="API rate limit reached",
        ):
            await provider.get_company_overview("IBM")


@pytest.mark.anyio
async def test_company_overview_handles_missing_company():
    provider = create_provider()

    fake_response = {}

    mock_response = create_mock_response(
        fake_response
    )

    with patch(
        "httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        with pytest.raises(
            CompanyDataError,
            match="No company information found",
        ):
            await provider.get_company_overview(
                "UNKNOWN"
            )