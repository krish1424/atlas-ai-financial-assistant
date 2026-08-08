from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Message


class MessageRepository:

    @staticmethod
    def create(
        db: Session,
        conversation_id: int,
        user_id: int,
        role: str,
        content: str,
    ) -> Message:

        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content,
        )

        db.add(message)
        db.flush()

        return message

    @staticmethod
    def get_conversation_messages(
        db: Session,
        conversation_id: int,
    ) -> list[Message]:

        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )

        return list(db.scalars(statement).all())