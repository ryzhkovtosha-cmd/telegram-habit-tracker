"""
Хранилище JWT-токенов с привязкой к telegram_id.
"""

import sqlite3
import os

DB_PATH = os.getenv("TOKEN_DB_PATH", "tokens.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            chat_id INTEGER PRIMARY KEY,
            token TEXT NOT NULL,
            telegram_id INTEGER NOT NULL
        )
    """)
    conn.commit()
    return conn

def save_token(chat_id: int, token: str, telegram_id: int):
    """Сохраняет токен и telegram_id."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO tokens (chat_id, token, telegram_id) VALUES (?, ?, ?) "
        "ON CONFLICT(chat_id) DO UPDATE SET token = excluded.token, "
        "telegram_id = excluded.telegram_id",
        (chat_id, token, telegram_id)
    )
    conn.commit()
    conn.close()

def get_token(chat_id: int) -> str | None:
    conn = get_connection()
    cursor = conn.execute("SELECT token FROM tokens WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_telegram_id(chat_id: int) -> int | None:
    """Возвращает telegram_id для данного чата."""
    conn = get_connection()
    cursor = conn.execute("SELECT telegram_id FROM tokens WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def delete_token(chat_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM tokens WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

def get_all_chat_ids() -> list[int]:
    """Возвращает список всех chat_id, для которых сохранены токены."""
    conn = get_connection()
    cursor = conn.execute("SELECT chat_id FROM tokens")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]