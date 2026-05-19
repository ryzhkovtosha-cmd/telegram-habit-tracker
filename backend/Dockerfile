FROM python:3.11-slim

WORKDIR /app

# Копируем и устанавливаем зависимости через pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]