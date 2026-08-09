from google import genai

from app.ai.providers.base import AIProvider
from app.config.settings import get_settings


class GeminiProvider(AIProvider):
    """Gemini implementation of the Atlas AI provider."""

    def __init__(self):
        settings = get_settings()

        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

        self.model = settings.gemini_model

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        """Generate a response using Gemini."""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=user_message,
            config={
                "system_instruction": system_prompt,
            },
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text.strip()