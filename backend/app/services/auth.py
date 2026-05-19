"""
Сервис аутентификации: регистрация и создание JWT.
"""
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models.user import User

async def get_or_create_user(telegram_id: int, username: str | None, db: AsyncSession) -> User:
    """Находит или создаёт пользователя по Telegram ID."""
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalars().first()
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user

def create_access_token(telegram_id: int) -> str:
    """Генерирует JWT с идентификатором пользователя."""
    payload = {"sub": str(telegram_id)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)