"""
Модуль конфигурации бота.
Загружает настройки из переменных окружения, заданных в docker-compose.yml или .env.
"""

import os

# Токен Telegram-бота, полученный от @BotFather.
# Если переменная окружения не задана, используется значение по умолчанию (необходимо заменить на реальный).
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

# Базовый URL API-сервера FastAPI.
# Внутри Docker-сети сервис api слушает порт 8000, поэтому указываем http://api:8000.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")