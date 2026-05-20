"""
Модуль для взаимодействия с backend API.
Содержит универсальную функцию api_request и хранилище JWT-токенов пользователей.
"""

import requests
from config import API_BASE_URL   # импортируем базовый URL из конфига

# Хранилище токенов: ключ – ID чата (chat_id), значение – JWT-токен (строка).
# Токены сохраняются только в оперативной памяти процесса.
# При перезапуске контейнера бота все токены теряются,
# и пользователю потребуется повторно отправить /start.
user_tokens = {}

def get_token(chat_id: int) -> str | None:
    """Возвращает токен для указанного chat_id или None, если пользователь не авторизован."""
    return user_tokens.get(chat_id)

def api_request(method: str, endpoint: str, chat_id: int,
                json_data: dict | None = None, params: dict | None = None):
    """
    Выполняет HTTP-запрос к FastAPI от имени пользователя.

    Параметры:
        method: HTTP-метод ('GET', 'POST', 'PUT', 'DELETE').
        endpoint: путь API (например, '/habits/').
        chat_id: ID чата Telegram, используется для получения токена.
        json_data: словарь с JSON-телом запроса (для POST/PUT).
        params: словарь с query-параметрами (для GET).

    Возвращает:
        Словарь с JSON-ответом, если запрос успешен.
        None при ошибке или пустом ответе (204 No Content).
    """
    # Собираем полный URL
    url = f"{API_BASE_URL}{endpoint}"

    # Если для данного чата есть сохранённый токен, добавляем заголовок авторизации
    headers = {}
    token = get_token(chat_id)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        # Выполняем соответствующий запрос
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            resp = requests.post(url, json=json_data, headers=headers)
        elif method == "PUT":
            resp = requests.put(url, json=json_data, headers=headers)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers)
        else:
            # Неизвестный метод – возвращаем None
            return None

        # Если статус не 2xx, генерируется исключение
        resp.raise_for_status()

        # Если ответ 204 No Content (например, при удалении), возвращаем None
        if resp.status_code == 204:
            return None

        # Возвращаем распарсенный JSON
        return resp.json()

    except requests.RequestException as e:
        # Логируем ошибку (в production можно писать в файл или систему мониторинга)
        print(f"API error: {e}")
        return None