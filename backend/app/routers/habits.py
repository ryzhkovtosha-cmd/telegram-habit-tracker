from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.habit import (
    HabitCreate, HabitUpdate, HabitOut, DailyHabitOut, DailyCompleteRequest
)
from app.services import habit as habit_service

router = APIRouter(prefix="/habits", tags=["habits"])

@router.get("/", response_model=list[HabitOut])
async def list_habits(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Список активных привычек пользователя."""
    habits = await habit_service.get_habits(user.id, db)
    return habits

@router.post("/", response_model=HabitOut, status_code=201)
async def create_habit(
    data: HabitCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание новой привычки."""
    habit = await habit_service.create_habit(user.id, data.name, data.description, db)
    return habit

@router.put("/{habit_id}", response_model=HabitOut)
async def update_habit(
    habit_id: int,
    data: HabitUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Редактирование привычки."""
    habit = await habit_service.update_habit(habit_id, user.id, db, data.name, data.description)
    if not habit:
        raise HTTPException(status_code=404, detail="Привычка не найдена")
    return habit

@router.delete("/{habit_id}", status_code=204)
async def delete_habit(
    habit_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление привычки."""
    success = await habit_service.delete_habit(habit_id, user.id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Привычка не найдена")
    return None

@router.get("/daily", response_model=list[DailyHabitOut])
async def get_daily_habits(
    target_date: date | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка привычек на конкретную дату (по умолчанию – сегодня)."""
    if target_date is None:
        target_date = date.today()
    records = await habit_service.get_daily_habits(user.id, target_date, db)
    result = []
    for rec in records:
        result.append(
            DailyHabitOut(
                id=rec.id,
                habit_id=rec.habit_id,
                date=rec.date,
                completed=rec.completed,
                habit_name=rec.habit.name
            )
        )
    return result

@router.post("/daily/{habit_id}/complete", response_model=DailyHabitOut)
async def complete_habit(
    habit_id: int,
    data: DailyCompleteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отметка выполнения привычки на указанную дату."""
    record = await habit_service.mark_habit_completed(habit_id, user.id, data.date, db)
    if not record:
        raise HTTPException(status_code=404, detail="Привычка не найдена или уже достигла цели")
    return DailyHabitOut(
        id=record.id,
        habit_id=record.habit_id,
        date=record.date,
        completed=record.completed,
        habit_name=record.habit.name
    )

@router.post("/daily/{habit_id}/fail", response_model=DailyHabitOut)
async def fail_habit(
    habit_id: int,
    data: DailyCompleteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    record = await habit_service.mark_habit_failed(habit_id, user.id, data.date, db)
    if not record:
        raise HTTPException(status_code=404, detail="Привычка не найдена")
    return DailyHabitOut(
        id=record.id,
        habit_id=record.habit_id,
        date=record.date,
        completed=record.completed,
        habit_name=record.habit.name
    )