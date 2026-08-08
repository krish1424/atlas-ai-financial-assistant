from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Conversation


class ConversationRepository:

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        title: str | None = None,
    ) -> Conversation:

        conversation = Conversation(
            user_id=user_id,
            title=title,
        )

        db.add(conversation)
        db.flush()

        return conversation

    @staticmethod
    def get_by_id(
        db: Session,
        conversation_id: int,
    ) -> Conversation | None:

        statement = select(Conversation).where(
            Conversation.id == conversation_id
        )

        return db.scalar(statement)

    @staticmethod
    def get_user_conversations(
        db: Session,
        user_id: int,
    ) -> list[Conversation]:

        statement = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )

        return list(db.scalars(statement).all())