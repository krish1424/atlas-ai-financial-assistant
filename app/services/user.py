from sqlalchemy.orm import Session

from app.database.models import User
from app.repositories.user_repository import UserRepository


class UserService:

    @staticmethod
    def get_or_create_user(
        db: Session,
        telegram_user_id: int,
        username: str | None = None,
        first_name: str | None = None,
    ) -> User:

        user = UserRepository.get_by_telegram_id(
            db=db,
            telegram_user_id=telegram_user_id,
        )

        if user:
            return user

        return UserRepository.create(
            db=db,
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
        )