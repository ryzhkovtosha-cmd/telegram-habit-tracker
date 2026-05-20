"""
Обработчики для управления привычками:
- просмотр списка (/habits)
- создание (/add)
- редактирование (/edit)
- удаление (/delete)
"""

import telebot
from .api_client import api_request

def register_habits(bot):
    """Регистрирует все обработчики, связанные с CRUD привычек."""

    # ---------- Просмотр списка привычек ----------
    @bot.message_handler(commands=['habits'])
    def list_habits(message):
        """Отправляет список всех активных привычек пользователя (completion_count < 21)."""
        resp = api_request("GET", "/habits/", message.chat.id)
        if resp is None:
            bot.send_message(message.chat.id, "Ошибка получения данных.")
            return
        if not resp:
            bot.send_message(message.chat.id, "У вас пока нет привычек.")
            return

        # Формируем текст: название привычки и прогресс (выполнено/21)
        text = "Ваши привычки:\n"
        for h in resp:
            text += f"• {h['name']} (выполнено {h['completion_count']}/21)\n"
        bot.send_message(message.chat.id, text)

    # ---------- Добавление привычки (пошаговый диалог) ----------
    @bot.message_handler(commands=['add'])
    def add_habit_start(message):
        """Начинает диалог добавления: запрашивает название."""
        msg = bot.send_message(message.chat.id, "Введите название привычки:")
        bot.register_next_step_handler(msg, process_add_name)

    def process_add_name(message):
        """Обрабатывает введённое название, запрашивает описание."""
        name = message.text.strip()
        msg = bot.send_message(
            message.chat.id,
            "Введите описание (или '-' чтобы пропустить):"
        )
        bot.register_next_step_handler(msg, process_add_description, name)

    def process_add_description(message, name):
        """Обрабатывает описание и отправляет запрос на создание привычки."""
        desc = message.text.strip()
        if desc == '-':
            desc = None   # пропуск описания

        json_data = {"name": name}
        if desc:
            json_data["description"] = desc

        resp = api_request("POST", "/habits/", message.chat.id, json_data=json_data)
        if resp:
            bot.send_message(message.chat.id, f"Привычка '{resp['name']}' создана.")
        else:
            bot.send_message(message.chat.id, "Ошибка при создании привычки.")

    # ---------- Редактирование привычки (через inline-кнопки) ----------
    @bot.message_handler(commands=['edit'])
    def edit_habit_start(message):
        """Выводит список привычек для выбора редактируемой."""
        resp = api_request("GET", "/habits/", message.chat.id)
        if not resp:
            bot.send_message(message.chat.id, "Нет привычек для редактирования.")
            return

        # Создаём клавиатуру с кнопками для каждой привычки
        keyboard = telebot.types.InlineKeyboardMarkup()
        for h in resp:
            # callback_data содержит префикс "edit_" и ID привычки
            keyboard.add(
                telebot.types.InlineKeyboardButton(
                    h['name'], callback_data=f"edit_{h['id']}"
                )
            )
        bot.send_message(message.chat.id, "Выберите привычку для редактирования:",
                         reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
    def edit_select(call):
        """Обрабатывает выбор привычки из списка, запрашивает новое название."""
        # Извлекаем ID привычки из callback_data (например, "edit_5")
        habit_id = int(call.data.split("_")[1])
        msg = bot.send_message(
            call.message.chat.id,
            "Введите новое название (или '-' чтобы не менять):"
        )
        # Передаём habit_id в следующий шаг
        bot.register_next_step_handler(msg, process_edit_name, habit_id)

    def process_edit_name(message, habit_id):
        """Принимает новое название, запрашивает новое описание."""
        new_name = message.text.strip()
        if new_name == '-':
            new_name = None
        msg = bot.send_message(
            message.chat.id,
            "Введите новое описание (или '-' чтобы не менять):"
        )
        bot.register_next_step_handler(msg, process_edit_description, habit_id, new_name)

    def process_edit_description(message, habit_id, new_name):
        """Отправляет PUT-запрос с обновлёнными данными."""
        new_desc = message.text.strip()
        if new_desc == '-':
            new_desc = None

        # Формируем тело только с теми полями, которые нужно изменить
        json_data = {}
        if new_name:
            json_data['name'] = new_name
        if new_desc:
            json_data['description'] = new_desc

        resp = api_request("PUT", f"/habits/{habit_id}", message.chat.id,
                           json_data=json_data)
        if resp:
            bot.send_message(message.chat.id, "Привычка обновлена.")
        else:
            bot.send_message(message.chat.id, "Ошибка при обновлении.")

    # ---------- Удаление привычки (через inline-кнопки с подтверждением) ----------
    @bot.message_handler(commands=['delete'])
    def delete_habit_start(message):
        """Выводит список привычек с кнопками для удаления."""
        resp = api_request("GET", "/habits/", message.chat.id)
        if not resp:
            bot.send_message(message.chat.id, "Нет привычек для удаления.")
            return

        keyboard = telebot.types.InlineKeyboardMarkup()
        for h in resp:
            # Кнопка с эмодзи корзины и названием, callback_data = "delete_<id>"
            keyboard.add(
                telebot.types.InlineKeyboardButton(
                    f"❌ {h['name']}", callback_data=f"delete_{h['id']}"
                )
            )
        bot.send_message(message.chat.id, "Выберите привычку для удаления:",
                         reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
    def delete_confirm(call):
        """Удаляет привычку по ID, полученному из callback_data."""
        habit_id = int(call.data.split("_")[1])
        resp = api_request("DELETE", f"/habits/{habit_id}", call.message.chat.id)

        if resp is None:   # API вернул 204 No Content – успех
            bot.answer_callback_query(call.id, "Привычка удалена.")
            # Редактируем исходное сообщение, убирая клавиатуру
            bot.edit_message_text(
                "Привычка удалена.",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, "Ошибка удаления.")