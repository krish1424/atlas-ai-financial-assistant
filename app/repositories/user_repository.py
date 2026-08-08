from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import User


class UserRepository:

    @staticmethod
    def get_by_telegram_id(
        db: Session,
        telegram_user_id: int,
    ) -> User | None:
        statement = select(User).where(
            User.telegram_user_id == telegram_user_id
        )

        return db.scalar(statement)

    @staticmethod
    def create(
        db: Session,
        telegram_user_id: int,
        username: str | None = None,
        first_name: str | None = None,
    ) -> User:

        user = User(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
        )

        db.add(user)
        db.flush()

        return user