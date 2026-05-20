"""
Модуль планировщика для отправки ежедневных напоминаний.
Использует APScheduler (BackgroundScheduler), который работает в фоновом потоке.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from api_client import user_tokens   # словарь chat_id → токен, чтобы знать, кому отправлять

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
        Проходит по всем chat_id из user_tokens и пытается отправить сообщение.
        """
        # Делаем копию списка ключей, т.к. словарь может меняться во время итерации
        for chat_id in list(user_tokens.keys()):
            try:
                bot.send_message(
                    chat_id,
                    "⏰ Не забудьте отметить выполнение привычек! /daily"
                )
            except Exception as e:
                # Ошибка может возникнуть, если пользователь заблокировал бота и т.п.
                print(f"Ошибка отправки напоминания {chat_id}: {e}")

    # Добавляем задание: cron-выражение 'hour=9, minute=0' – каждый день в 9:00
    scheduler.add_job(send_reminders, 'cron', hour=9, minute=0)

    # Запускаем планировщик в фоне (не блокирует основной поток)
    scheduler.start()