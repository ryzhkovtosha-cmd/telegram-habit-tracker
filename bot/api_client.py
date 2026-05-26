
"""
HTTP-клиент с автоматическим восстановлением токена при 401.
"""

import requests
from config import API_BASE_URL
from token_storage import get_token, save_token, get_telegram_id

def refresh_token(chat_id: int) -> str | None:
    """
    Запрашивает новый токен для пользователя, используя сохранённый telegram_id.
    Вызывается при получении 401 ответа.
    """
    tid = get_telegram_id(chat_id)
    if tid is None:
        print(f"Не удалось обновить токен: отсутствует telegram_id для chat_id={chat_id}")
        return None
    try:
        resp = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={"telegram_id": tid, "username": None}
        )
        resp.raise_for_status()
        data = resp.json()
        new_token = data.get("access_token")
        if new_token:
            save_token(chat_id, new_token, tid)
            return new_token
    except requests.RequestException as e:
        print(f"Ошибка обновления токена: {e}")
    return None

def api_request(method: str, endpoint: str, chat_id: int,
                json_data: dict | None = None, params: dict | None = None) -> dict | None:
    """
    Выполняет HTTP-запрос с автоматическим повтором при истечении токена.
    """
    url = f"{API_BASE_URL}{endpoint}"
    token = get_token(chat_id)
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        # Первая попытка
        resp = _make_request(method, url, headers, json_data, params)
        if resp.status_code == 401:
            print("Токен истёк, обновляю...")
            new_token = refresh_token(chat_id)
            if new_token:
                headers["Authorization"] = f"Bearer {new_token}"
                resp = _make_request(method, url, headers, json_data, params)

        resp.raise_for_status()
        if resp.status_code == 204:
            return None
        return resp.json()
    except requests.RequestException as e:
        print(f"API error [{method} {endpoint}]: {e}")
        return None

def _make_request(method, url, headers, json_data, params):
    """Вспомогательная функция для выполнения одного HTTP-запроса."""
    if method == "GET":
        return requests.get(url, headers=headers, params=params)
    elif method == "POST":
        return requests.post(url, json=json_data, headers=headers)
    elif method == "PUT":
        return requests.put(url, json=json_data, headers=headers)
    elif method == "DELETE":
        return requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")