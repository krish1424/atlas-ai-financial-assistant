from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Base interface for AI providers."""

    @abstractmethod
    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        """Generate an AI response."""
        raise NotImplementedError