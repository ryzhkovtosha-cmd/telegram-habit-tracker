from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, TokenResponse
from app.services.auth import get_or_create_user, create_access_token
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация или вход пользователя, возвращает JWT."""
    user = await get_or_create_user(user_data.telegram_id, user_data.username, db)
    token = create_access_token(user.telegram_id)
    return {"access_token": token}