from sqlalchemy.orm import Session

from app.database.models import Conversation, Message
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository


class ConversationService:

    @staticmethod
    def create_conversation(
        db: Session,
        user_id: int,
        title: str | None = None,
    ) -> Conversation:

        return ConversationRepository.create(
            db=db,
            user_id=user_id,
            title=title,
        )

    @staticmethod
    def add_message(
        db: Session,
        conversation_id: int,
        user_id: int,
        role: str,
        content: str,
    ) -> Message:

        if role not in {"user", "assistant", "system", "tool"}:
            raise ValueError(
                f"Invalid message role: {role}"
            )

        if not content.strip():
            raise ValueError(
                "Message content cannot be empty."
            )

        return MessageRepository.create(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content,
        )

    @staticmethod
    def get_history(
        db: Session,
        conversation_id: int,
    ) -> list[Message]:

        return MessageRepository.get_conversation_messages(
            db=db,
            conversation_id=conversation_id,
        )

    @staticmethod
    def get_or_create_conversation(
        db: Session,
        user_id: int,
    ) -> Conversation:

        conversation = ConversationRepository.get_latest_for_user(
            db=db,
            user_id=user_id,
        )

        if conversation:
            return conversation

        return ConversationRepository.create(
            db=db,
            user_id=user_id,
            title="Atlas Conversation",
        )