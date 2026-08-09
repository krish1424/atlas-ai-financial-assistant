from dataclasses import dataclass


@dataclass
class ConversationMessage:
    role: str
    content: str


class MemoryManager:
    """
    Manages conversation context for the AI assistant.

    Database persistence is handled by the existing repository layer.
    This class is responsible only for preparing context for the AI.
    """

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages

    def build_context(
        self,
        messages: list[ConversationMessage],
    ) -> list[dict]:
        """
        Convert stored messages into LLM-compatible messages.
        """

        recent_messages = messages[-self.max_messages:]

        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in recent_messages
        ]