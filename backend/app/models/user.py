"""
Модель пользователя.
"""
from sqlalchemy import Column, Integer, String, BigInteger
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    # JWT-токен не храним, он генерируется на лету