from fastapi import FastAPI
from app.routers import auth, habits
from app.database import engine, Base, AsyncSessionLocal
from app.services.habit import daily_habits_transfer_all_users
from apscheduler.schedulers.asyncio import AsyncIOScheduler

app = FastAPI(title="Habit Tracker API")

app.include_router(auth.router)
app.include_router(habits.router)

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def on_startup():
    # Создаём таблицы (для разработки, в продакшене — Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Запускаем ежедневный перенос привычек в 00:01
    scheduler.add_job(daily_habits_transfer_all_users, 'cron', hour=0, minute=1)
    scheduler.start()

@app.get("/")
async def root():
    return {"message": "API трекера привычек"}