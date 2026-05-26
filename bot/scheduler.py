"""
Модуль планировщика для отправки ежедневных напоминаний.
Использует APScheduler (BackgroundScheduler), который работает в фоновом потоке.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from token_storage import get_all_chat_ids   # получаем список chat_id из БД

def start_scheduler(bot):
    """
    Настраивает и запускает планировщик.
    Задача: каждый день в 9:00 (UTC) отправляет всем авторизованным пользователям
    сообщение с напоминанием отметить выполнение привычек.
    """
    scheduler = BackgroundScheduler()

    def send_reminders():
        """
        Функция, вызываемая по расписанию.
        Получает все chat_id из SQLite и пытается отправить сообщение.
        """
        for chat_id in get_all_chat_ids():
            try:
                bot.send_message(
                    chat_id,
                    "⏰ Не забудьте отметить выполнение привычек! /daily"
                )
            except Exception as e:
                # Ошибка может возникнуть, если пользователь заблокировал бота и т.п.
                print(f"Ошибка отправки напоминания {chat_id}: {e}")

    # Каждый день в 9:00
    scheduler.add_job(send_reminders, 'cron', hour=9, minute=0)
    scheduler.start()