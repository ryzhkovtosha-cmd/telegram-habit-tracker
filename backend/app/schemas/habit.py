from pydantic import BaseModel
from datetime import date
from typing import Optional

class HabitCreate(BaseModel):
    name: str
    description: Optional[str] = None

class HabitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class HabitOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    completion_count: int

    class Config:
        from_attributes = True

class DailyHabitOut(BaseModel):
    id: int
    habit_id: int
    date: date
    completed: bool
    habit_name: str

class DailyCompleteRequest(BaseModel):
    date: date