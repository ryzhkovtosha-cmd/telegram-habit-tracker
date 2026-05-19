"""
Telegram-бот для трекинга привычек.
Взаимодействует с backend API, сохраняет токены пользователей.
"""
import telebot
import requests
import os
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
import time

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

bot = telebot.TeleBot(BOT_TOKEN)
# Хранилище токенов: chat_id -> access_token
user_tokens = {}

@bot.message_handler(commands=['edit'])
def edit_habit_start(message):
    """Выводит список привычек для выбора редактирования."""
    resp = api_request("GET", "/habits/", message.chat.id)
    if not resp:
        bot.send_message(message.chat.id, "Нет привычек для редактирования.")
        return
    keyboard = telebot.types.InlineKeyboardMarkup()
    for h in resp:
        keyboard.add(telebot.types.InlineKeyboardButton(
            h['name'], callback_data=f"edit_{h['id']}"
        ))
    bot.send_message(message.chat.id, "Выберите привычку для редактирования:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def edit_habit_select(call):
    habit_id = int(call.data.split("_")[1])
    msg = bot.send_message(call.message.chat.id, "Введите новое название (или '-' чтобы не менять):")
    bot.register_next_step_handler(msg, process_edit_name, habit_id)

def process_edit_name(message, habit_id):
    new_name = message.text.strip()
    if new_name == '-':
        new_name = None
    msg = bot.send_message(message.chat.id, "Введите новое описание (или '-' чтобы не менять):")
    bot.register_next_step_handler(msg, process_edit_description, habit_id, new_name)

def process_edit_description(message, habit_id, new_name):
    new_desc = message.text.strip()
    if new_desc == '-':
        new_desc = None
    json_data = {}
    if new_name:
        json_data['name'] = new_name
    if new_desc:
        json_data['description'] = new_desc
    resp = api_request("PUT", f"/habits/{habit_id}", message.chat.id, json_data=json_data)
    if resp:
        bot.send_message(message.chat.id, "Привычка обновлена.")
    else:
        bot.send_message(message.chat.id, "Ошибка при обновлении.")

# Команда удаления
@bot.message_handler(commands=['delete'])
def delete_habit_start(message):
    resp = api_request("GET", "/habits/", message.chat.id)
    if not resp:
        bot.send_message(message.chat.id, "Нет привычек для удаления.")
        return
    keyboard = telebot.types.InlineKeyboardMarkup()
    for h in resp:
        keyboard.add(telebot.types.InlineKeyboardButton(
            f"❌ {h['name']}", callback_data=f"delete_{h['id']}"
        ))
    bot.send_message(message.chat.id, "Выберите привычку для удаления:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
def delete_habit_confirm(call):
    habit_id = int(call.data.split("_")[1])
    resp = api_request("DELETE", f"/habits/{habit_id}", call.message.chat.id)
    if resp is None:  # 204 No Content
        bot.answer_callback_query(call.id, "Привычка удалена.")
        bot.edit_message_text("Привычка удалена.", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Ошибка удаления.")
def get_token(chat_id):
    return user_tokens.get(chat_id)

def api_request(method, endpoint, chat_id, json_data=None, params=None):
    """Выполняет запрос к API с авторизацией."""
    token = get_token(chat_id)
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            resp = requests.post(url, json=json_data, headers=headers)
        elif method == "PUT":
            resp = requests.put(url, json=json_data, headers=headers)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers)
        else:
            return None
        resp.raise_for_status()
        if resp.status_code == 204:
            return None
        return resp.json()
    except requests.RequestException as e:
        print(f"API error: {e}")
        return None

@bot.message_handler(commands=['start'])
def start_command(message):
    """Регистрирует пользователя и сохраняет токен."""
    telegram_id = message.from_user.id
    username = message.from_user.username
    resp = api_request("POST", "/auth/register", message.chat.id,
                       json_data={"telegram_id": telegram_id, "username": username})
    if resp and "access_token" in resp:
        user_tokens[message.chat.id] = resp["access_token"]
        bot.reply_to(message,
                     "✅ Авторизация успешна!\n\n"
                     "Доступные команды:\n"
                     "/habits — список привычек\n"
                     "/add — добавить привычку\n"
                     "/edit — редактировать привычку\n"
                     "/delete — удалить привычку\n"
                     "/daily — привычки на сегодня\n"
                     "/help — помощь и список команд"
                     )
    else:
        bot.reply_to(message, "Ошибка авторизации.")

@bot.message_handler(commands=['add'])
def add_habit(message):
    """Начинает диалог добавления привычки."""
    msg = bot.send_message(message.chat.id, "Введите название привычки:")
    bot.register_next_step_handler(msg, process_name)

def process_name(message):
    name = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введите описание (или отправьте '-', чтобы пропустить):")
    bot.register_next_step_handler(msg, process_description, name)

def process_description(message, name):
    desc = message.text.strip()
    if desc == '-':
        desc = None
    json_data = {"name": name}
    if desc:
        json_data["description"] = desc
    resp = api_request("POST", "/habits/", message.chat.id, json_data=json_data)
    if resp:
        bot.send_message(message.chat.id, f"Привычка '{resp['name']}' создана.")
    else:
        bot.send_message(message.chat.id, "Ошибка при создании привычки.")

@bot.message_handler(commands=['habits'])
def list_habits(message):
    """Показывает список всех активных привычек."""
    resp = api_request("GET", "/habits/", message.chat.id)
    if resp is None:
        bot.send_message(message.chat.id, "Ошибка получения данных.")
        return
    if not resp:
        bot.send_message(message.chat.id, "У вас пока нет привычек.")
        return
    text = "Ваши привычки:\n"
    for h in resp:
        text += f"• {h['name']} (выполнено {h['completion_count']}/21)\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['daily'])
def daily_habits(message):
    today = date.today().isoformat()
    resp = api_request("GET", "/habits/daily", message.chat.id, params={"target_date": today})
    if resp is None:
        bot.send_message(message.chat.id, "Ошибка загрузки списка.")
        return
    if not resp:
        bot.send_message(message.chat.id, "На сегодня привычек нет.")
        return

    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    for item in resp:
        status = "✅" if item["completed"] else "⬜"
        btn_done = telebot.types.InlineKeyboardButton(
            f"{status} {item['habit_name']}",
            callback_data=f"complete_{item['habit_id']}_{today}"
        )
        btn_fail = telebot.types.InlineKeyboardButton(
            "❌ Не выполнено",
            callback_data=f"fail_{item['habit_id']}_{today}"
        )
        keyboard.add(btn_done, btn_fail)
    bot.send_message(message.chat.id, "Привычки на сегодня:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("complete_"))
def handle_complete(call):
    """Обрабатывает нажатие кнопки выполнения."""
    parts = call.data.split("_")
    if len(parts) != 3:
        return
    habit_id = parts[1]
    target_date = parts[2]
    resp = api_request("POST", f"/habits/daily/{habit_id}/complete", call.message.chat.id,
                       json_data={"date": target_date})
    if resp:
        new_status = "✅" if resp["completed"] else "⬜"
        bot.answer_callback_query(call.id, f"Привычка отмечена как {new_status}")
        # Обновляем сообщение с кнопками
        daily_habits_command = lambda m: daily_habits(m)  # обновить список
        # Просто вызовем daily_habits ещё раз, изменив сообщение
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="Привычки на сегодня обновлены. Нажмите /daily для просмотра.")
    else:
        bot.answer_callback_query(call.id, "Ошибка при отметке.")

# Фоновое уведомление
def send_reminders():
    """Отправляет всем зарегистрированным пользователям напоминание."""
    for chat_id in list(user_tokens.keys()):
        try:
            bot.send_message(chat_id, "⏰ Не забудьте отметить выполнение привычек! /daily")
        except Exception as e:
            print(f"Ошибка отправки напоминания {chat_id}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(send_reminders, 'cron', hour=9, minute=0)  # каждый день в 9:00
scheduler.start()

@bot.callback_query_handler(func=lambda call: call.data.startswith("fail_"))
def handle_fail(call):
    parts = call.data.split("_")
    habit_id = parts[1]
    target_date = parts[2]
    # Пока у нас нет отдельного API для невыполнения, можно просто пропустить,
    # или добавить эндпоинт "fail". По ТЗ фиксация "не выполнил" должна быть.
    # Реализуем через тот же complete с completed=false (нужен новый endpoint)
    resp = api_request("POST", f"/habits/daily/{habit_id}/fail", call.message.chat.id,
                       json={"date": target_date})
    if resp:
        bot.answer_callback_query(call.id, "Привычка отмечена как невыполненная")
        bot.edit_message_text("Список обновлён. /daily", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Ошибка.")

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()