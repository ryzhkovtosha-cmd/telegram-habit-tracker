"""
Бизнес-логика для работы с привычками и ежедневным трекингом.
"""
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.user import User
from app.models.habit import Habit, DailyCompletion
from app.config import settings

async def create_habit(user_id: int, name: str, description: str | None, db: AsyncSession) -> Habit:
    """Создаёт новую привычку."""
    habit = Habit(user_id=user_id, name=name, description=description)
    db.add(habit)
    await db.commit()
    await db.refresh(habit)
    return habit

async def get_habits(user_id: int, db: AsyncSession) -> list[Habit]:
    """Возвращает все активные привычки пользователя."""
    result = await db.execute(
        select(Habit).where(Habit.user_id == user_id, Habit.completion_count < settings.HABIT_DAYS_GOAL)
    )
    return result.scalars().all()

async def update_habit(habit_id: int, user_id: int, db: AsyncSession, name: str | None, description: str | None) -> Habit | None:
    """Редактирует привычку."""
    habit = await db.get(Habit, habit_id)
    if not habit or habit.user_id != user_id:
        return None
    if name is not None:
        habit.name = name
    if description is not None:
        habit.description = description
    await db.commit()
    await db.refresh(habit)
    return habit

async def delete_habit(habit_id: int, user_id: int, db: AsyncSession) -> bool:
    """Удаляет привычку."""
    habit = await db.get(Habit, habit_id)
    if not habit or habit.user_id != user_id:
        return False
    await db.delete(habit)
    await db.commit()
    return True

from sqlalchemy.orm import selectinload   # добавьте в начало файла

async def get_daily_habits(user_id: int, target_date: date, db: AsyncSession) -> list[DailyCompletion]:
    """Возвращает ежедневные записи на дату, при необходимости создаёт их."""
    # Ищем существующие записи с загруженной привычкой
    result = await db.execute(
        select(DailyCompletion)
        .options(selectinload(DailyCompletion.habit))
        .join(DailyCompletion.habit)
        .where(
            Habit.user_id == user_id,
            DailyCompletion.date == target_date,
            Habit.completion_count < settings.HABIT_DAYS_GOAL
        )
    )
    records = result.scalars().all()
    if records:
        return records

    # Создаём новые записи для каждой активной привычки
    habits = await get_habits(user_id, db)
    new_records = []
    for habit in habits:
        rec = DailyCompletion(habit_id=habit.id, date=target_date, completed=False)
        rec.habit = habit   # сразу присваиваем объект привычки
        db.add(rec)
        new_records.append(rec)
    await db.commit()
    return new_records


async def mark_habit_completed(habit_id: int, user_id: int, target_date: date, db: AsyncSession) -> DailyCompletion | None:
    habit = await db.get(Habit, habit_id)
    if not habit or habit.user_id != user_id or habit.completion_count >= settings.HABIT_DAYS_GOAL:
        return None

    result = await db.execute(
        select(DailyCompletion).where(
            DailyCompletion.habit_id == habit_id,
            DailyCompletion.date == target_date
        )
    )
    record = result.scalars().first()
    if not record:
        record = DailyCompletion(habit_id=habit_id, date=target_date, completed=False)
        db.add(record)

    # Присоединяем объект привычки, чтобы не требовалась ленивая загрузка
    record.habit = habit

    if not record.completed:
        record.completed = True
        habit.completion_count += 1
        await db.commit()
        # refresh не делаем, чтобы не стереть присоединённый habit
    return record

async def daily_habits_transfer(user_id: int, db: AsyncSession) -> None:
    """
    Перенос привычек на следующий день.
    Вызывается планировщиком или при необходимости.
    """
    today = date.today()
    tomorrow = today + timedelta(days=1)
    active_habits = await get_habits(user_id, db)
    for habit in active_habits:
        # Проверяем, нет ли уже записи на завтра
        existing = await db.execute(
            select(DailyCompletion).where(
                DailyCompletion.habit_id == habit.id,
                DailyCompletion.date == tomorrow
            )
        )
        if not existing.scalars().first():
            rec = DailyCompletion(habit_id=habit.id, date=tomorrow, completed=False)
            db.add(rec)
    await db.commit()

async def mark_habit_failed(habit_id: int, user_id: int, target_date: date,
                            db: AsyncSession) -> DailyCompletion | None:
    habit = await db.get(Habit, habit_id)
    if not habit or habit.user_id != user_id or habit.completion_count >= settings.HABIT_DAYS_GOAL:
        return None
    result = await db.execute(
        select(DailyCompletion).where(
            DailyCompletion.habit_id == habit_id,
            DailyCompletion.date == target_date
        )
    )
    record = result.scalars().first()
    if not record:
        record = DailyCompletion(habit_id=habit_id, date=target_date, completed=False)
        record.habit = habit
        db.add(record)
    record.completed = False  # явно ставим не выполнено
    await db.commit()
    return record



async def daily_habits_transfer_all_users():
    """Переносит привычки всех пользователей на завтра."""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        users = (await db.execute(select(User))).scalars().all()
        for user in users:
            await daily_habits_transfer(user.id, db)