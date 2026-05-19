"""
Модели привычек и ежедневного трекинга.
"""
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    # Общее количество завершённых дней (для быстрого доступа)
    completion_count = Column(Integer, default=0)

    user = relationship("User", backref="habits")
    daily_records = relationship("DailyCompletion", back_populates="habit", cascade="all, delete-orphan")


class DailyCompletion(Base):
    __tablename__ = "daily_completions"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)

    habit = relationship("Habit", back_populates="daily_records")