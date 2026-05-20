# Базовый образ Python (лёгкая версия без лишних пакетов)
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем список зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код бота в контейнер
COPY . .

# Команда, которая выполняется при старте контейнера
CMD ["python", "bot.py"]