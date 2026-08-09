from dataclasses import dataclass

from google import genai
from google.genai import types

from app.ai.memory import ConversationMessage, MemoryManager
from app.ai.planner import Plan, create_plan
from app.ai.prompts import ATLAS_SYSTEM_PROMPT
from app.config.settings import get_settings


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
    4. Send context to Gemini.
    5. Return a clean response.
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
        """
        Create a deterministic execution plan.

        The planner will be expanded later with
        financial tools and AI-based routing.
        """

        return create_plan(message)

    def build_messages(
        self,
        user_message: str,
        conversation_history: list[ConversationMessage] | None = None,
    ) -> list[types.Content]:
        """
        Convert conversation history into Gemini-compatible messages.
        """

        history = conversation_history or []

        context = self.memory.build_context(history)

        messages: list[types.Content] = []

        for message in context:
            role = message["role"]

            # Gemini uses "model" instead of "assistant".
            if role == "assistant":
                role = "model"

            # System messages are handled separately through
            # GenerateContentConfig.system_instruction.
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

    async def generate_response(
        self,
        messages: list[types.Content],
    ) -> str:
        """
        Send the conversation to Gemini and return
        the generated text response.
        """

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=ATLAS_SYSTEM_PROMPT,
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
        """
        Process a user request through the Atlas AI pipeline.
        """

        if not user_message or not user_message.strip():
            raise ValueError(
                "User message cannot be empty."
            )

        user_message = user_message.strip()

        # Step 1: Understand the request.
        plan = self.create_plan(user_message)

        # Step 2: Prepare conversation context.
        messages = self.build_messages(
            user_message=user_message,
            conversation_history=conversation_history,
        )

        # Step 3: Generate the AI response.
        response = await self.generate_response(
            messages=messages
        )

        return AgentResponse(
            message=response,
            plan=plan,
        )