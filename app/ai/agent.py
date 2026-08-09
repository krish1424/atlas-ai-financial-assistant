from dataclasses import dataclass

from google import genai
from google.genai import types

from app.ai.memory import ConversationMessage, MemoryManager
from app.ai.planner import Plan, Intent, create_plan
from app.ai.prompts import ATLAS_SYSTEM_PROMPT
from app.config.settings import get_settings
from app.tools.financial.company_data import (
    CompanyDataError,
    get_company_overview,
)
from app.tools.financial.market_data import (
    MarketDataError,
    get_stock_quote,
)


@dataclass
class AgentResponse:
    message: str
    plan: Plan


class AtlasAgent:
    """
    Main orchestration layer for Atlas.

    Responsibilities:
    1. Understand the user's request.
    2. Create an execution plan.
    3. Prepare conversation context.
    4. Execute required tools.
    5. Send verified information to Gemini.
    6. Return a clean response.
    """

    def __init__(self):
        self.settings = get_settings()

        if not self.settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self.memory = MemoryManager()

        self.client = genai.Client(
            api_key=self.settings.gemini_api_key
        )

        self.model = self.settings.gemini_model

    def create_plan(self, message: str) -> Plan:
        """Create an execution plan."""

        return create_plan(message)

    def build_messages(
        self,
        user_message: str,
        conversation_history: list[ConversationMessage] | None = None,
    ) -> list[types.Content]:
        """Convert conversation history into Gemini messages."""

        history = conversation_history or []

        context = self.memory.build_context(history)

        messages: list[types.Content] = []

        for message in context:
            role = message["role"]

            if role == "assistant":
                role = "model"

            if role == "system":
                continue

            messages.append(
                types.Content(
                    role=role,
                    parts=[
                        types.Part.from_text(
                            text=message["content"]
                        )
                    ],
                )
            )

        messages.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=user_message
                    )
                ],
            )
        )

        return messages

    async def get_market_data_context(
        self,
        plan: Plan,
    ) -> str:
        """Retrieve verified stock-market data."""

        if plan.intent != Intent.MARKET_DATA:
            return ""

        if not plan.symbol:
            return (
                "No stock symbol could be identified. "
                "Do not guess a symbol. Ask the user for "
                "a company name or stock ticker."
            )

        try:
            quote = await get_stock_quote(plan.symbol)

        except MarketDataError as exc:
            return (
                f"Market data could not be retrieved for "
                f"{plan.symbol}.\n\n"
                f"Tool error: {exc}\n\n"
                "Do not invent or estimate a stock price."
            )

        return (
            "VERIFIED MARKET DATA FROM ALPHA VANTAGE\n"
            f"Symbol: {quote.symbol}\n"
            f"Latest available price: {quote.price}\n"
            f"Change: {quote.change}\n"
            f"Change percent: {quote.change_percent}\n"
            f"Volume: {quote.volume}\n"
            f"Latest trading day: {quote.latest_trading_day}\n\n"
            "IMPORTANT:\n"
            "- Use these values instead of internal knowledge.\n"
            "- Do not invent additional market figures.\n"
            "- Clearly state that this is the latest available "
            "provider data and may not be real-time."
        )

    async def get_company_data_context(
        self,
        plan: Plan,
    ) -> str:
        """Retrieve verified company fundamentals."""

        if plan.intent != Intent.COMPANY_RESEARCH:
            return ""

        if not plan.symbol:
            return (
                "No company symbol could be identified from the "
                "user's request. Do not guess a company. Ask the "
                "user which company they mean."
            )

        try:
            company = await get_company_overview(
                plan.symbol
            )

        except CompanyDataError as exc:
            return (
                f"Company information could not be retrieved "
                f"for {plan.symbol}.\n\n"
                f"Tool error: {exc}\n\n"
                "Do not invent company financial information."
            )

        return (
            "VERIFIED COMPANY DATA FROM ALPHA VANTAGE\n"
            f"Symbol: {company.symbol}\n"
            f"Company: {company.name}\n"
            f"Exchange: {company.exchange}\n"
            f"Country: {company.country}\n"
            f"Sector: {company.sector}\n"
            f"Industry: {company.industry}\n"
            f"Market capitalization: {company.market_cap}\n"
            f"Revenue TTM: {company.revenue_ttm}\n"
            f"Profit margin: {company.profit_margin}\n"
            f"P/E ratio: {company.pe_ratio}\n"
            f"Dividend yield: {company.dividend_yield}\n\n"
            "IMPORTANT:\n"
            "- Use these values instead of internal knowledge.\n"
            "- Do not invent additional financial figures.\n"
            "- Explain figures clearly when presenting them."
        )

    async def get_tool_context(
        self,
        plan: Plan,
    ) -> str:
        """
        Execute the appropriate tool based on the plan.
        """

        if not plan.requires_tool:
            return ""

        if plan.intent == Intent.MARKET_DATA:
            return await self.get_market_data_context(plan)

        if plan.intent == Intent.COMPANY_RESEARCH:
            return await self.get_company_data_context(plan)

        return ""

    async def generate_response(
        self,
        messages: list[types.Content],
        tool_context: str = "",
    ) -> str:
        """Generate the final Gemini response."""

        system_instruction = ATLAS_SYSTEM_PROMPT

        if tool_context:
            system_instruction += (
                "\n\n"
                "TOOL EXECUTION CONTEXT\n"
                "The following information was retrieved by "
                "Atlas tools. Treat it as verified external "
                "data for this response.\n\n"
                f"{tool_context}"
            )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=1000,
            ),
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text.strip()

    async def process(
        self,
        user_message: str,
        conversation_history: list[ConversationMessage] | None = None,
    ) -> AgentResponse:
        """Process a user request through Atlas."""

        if not user_message or not user_message.strip():
            raise ValueError(
                "User message cannot be empty."
            )

        user_message = user_message.strip()

        # 1. Create execution plan.
        plan = self.create_plan(user_message)

        # 2. Prepare conversation context.
        messages = self.build_messages(
            user_message=user_message,
            conversation_history=conversation_history,
        )

        # 3. Execute required tools.
        tool_context = await self.get_tool_context(plan)

        # 4. Generate final response.
        response = await self.generate_response(
            messages=messages,
            tool_context=tool_context,
        )

        return AgentResponse(
            message=response,
            plan=plan,
        )