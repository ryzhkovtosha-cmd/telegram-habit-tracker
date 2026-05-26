"""
Конфигурация Alembic для асинхронного движка SQLAlchemy.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine

from alembic import context

# Импорт моделей и базы
from app.database import Base
from app.models.user import User
from app.models.habit import Habit, DailyCompletion
from app.config import settings

# Загружаем конфигурацию Alembic из файла
config = context.config

# Настраиваем логгер
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Устанавливаем метаданные моделей для автогенерации миграций
target_metadata = Base.metadata

def get_url():
    """Возвращает URL подключения к БД из настроек проекта."""
    return settings.DATABASE_URL

def run_migrations_offline() -> None:
    """Запуск миграций в офлайн-режиме (без подключения к БД)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    """Выполнение миграций через синхронное соединение."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """Асинхронная обёртка для запуска миграций."""
    # Создаём асинхронный движок
    connectable = create_async_engine(
        get_url(),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Передаём синхронную обёртку в run_sync
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Запуск миграций в онлайн-режиме с подключением к БД."""
    # Запускаем асинхронную функцию через asyncio.run
    asyncio.run(run_async_migrations())

# Определяем, в каком режиме запускать
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()