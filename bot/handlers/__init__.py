"""
Инициализация пакета handlers.
Содержит функцию register_handlers, которая регистрирует все обработчики команд и callback-ов.
"""

from .start import register_start
from .habits import register_habits
from .daily import register_daily

def register_handlers(bot):
    """
    Принимает объект бота и вызывает функции регистрации из каждого модуля.
    Каждая функция добавляет декораторы @bot.message_handler и @bot.callback_query_handler.
    """
    register_start(bot)   # команды /start, /help
    register_habits(bot)  # /habits, /add, /edit, /delete
    register_daily(bot)   # /daily и обработка кнопок выполнения