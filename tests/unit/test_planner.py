from app.ai.planner import create_plan


def test_market_data_plan():
    plan = create_plan(
        "What is Apple's stock price?"
    )

    assert plan.intent == "market_data"
    assert plan.symbol == "AAPL"
    assert plan.requires_live_data is True
    assert plan.requires_tool is True


def test_market_data_with_dollar_symbol():
    plan = create_plan(
        "What is $NVDA trading at?"
    )

    assert plan.intent == "market_data"
    assert plan.symbol == "NVDA"
    assert plan.requires_live_data is True
    assert plan.requires_tool is True


def test_company_research_plan():
    plan = create_plan(
        "Tell me about IBM's business"
    )

    assert plan.intent == "company_research"
    assert plan.symbol == "IBM"
    assert plan.requires_live_data is True
    assert plan.requires_tool is True


def test_news_plan():
    plan = create_plan(
        "What is the latest news about IBM?"
    )

    assert plan.intent == "news"
    assert plan.symbol == "IBM"
    assert plan.requires_live_data is True
    assert plan.requires_tool is True


def test_general_question():
    plan = create_plan(
        "What is revenue?"
    )

    assert plan.intent == "general"
    assert plan.symbol is None
    assert plan.requires_live_data is False
    assert plan.requires_tool is False