"""
Обработчики ежедневного трекинга:
- /daily – вывод списка привычек на сегодня с кнопками выполнения/невыполнения
- callback для отметки «выполнено»
- callback для отметки «не выполнено»
После любой отметки сообщение обновляется, показывая актуальный список.
"""

from datetime import date
import telebot
from api_client import api_request

def register_daily(bot):
    # Вспомогательная функция, чтобы не дублировать код построения клавиатуры
    def build_daily_keyboard(chat_id):
        today = date.today().isoformat()
        resp = api_request("GET", "/habits/daily", chat_id,
                           params={"target_date": today})
        if resp is None:
            return None, "Ошибка загрузки списка."
        if not resp:
            return None, "На сегодня привычек нет."

        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        for item in resp:
            status = "✅" if item["completed"] else "⬜"
            habit_name = item['habit_name']
            habit_id = item['habit_id']
            btn_done = telebot.types.InlineKeyboardButton(
                f"{status} {habit_name}",
                callback_data=f"complete_{habit_id}_{today}"
            )
            btn_fail = telebot.types.InlineKeyboardButton(
                "❌ Не выполнено",
                callback_data=f"fail_{habit_id}_{today}"
            )
            keyboard.add(btn_done, btn_fail)
        return keyboard, None   # второе значение — текст ошибки, если есть

    @bot.message_handler(commands=['daily'])
    def daily_habits(message):
        keyboard, error_msg = build_daily_keyboard(message.chat.id)
        if error_msg:
            bot.send_message(message.chat.id, error_msg)
            return
        bot.send_message(message.chat.id, "Привычки на сегодня:", reply_markup=keyboard)

    # ---------- Обработка «Выполнено» ----------
    @bot.callback_query_handler(func=lambda call: call.data.startswith("complete_"))
    def handle_complete(call):
        parts = call.data.split("_")
        if len(parts) != 3:
            return
        habit_id = parts[1]
        target_date = parts[2]
        resp = api_request(
            "POST", f"/habits/daily/{habit_id}/complete",
            call.message.chat.id,
            json_data={"date": target_date}
        )
        if resp:
            bot.answer_callback_query(call.id, "✅ Выполнено!")
            # Обновляем то же сообщение – показываем новый список с кнопками
            keyboard, error_msg = build_daily_keyboard(call.message.chat.id)
            if error_msg:
                bot.edit_message_text(error_msg,
                                      call.message.chat.id, call.message.message_id)
            else:
                bot.edit_message_text("Привычки на сегодня:",
                                      call.message.chat.id, call.message.message_id,
                                      reply_markup=keyboard)
        else:
            bot.answer_callback_query(call.id, "Ошибка при отметке.")

    # ---------- Обработка «Не выполнено» ----------
    @bot.callback_query_handler(func=lambda call: call.data.startswith("fail_"))
    def handle_fail(call):
        parts = call.data.split("_")
        if len(parts) != 3:
            return
        habit_id = parts[1]
        target_date = parts[2]
        resp = api_request(
            "POST", f"/habits/daily/{habit_id}/fail",
            call.message.chat.id,
            json_data={"date": target_date}
        )
        if resp:
            bot.answer_callback_query(call.id, "❌ Отмечено как не выполнено.")
            keyboard, error_msg = build_daily_keyboard(call.message.chat.id)
            if error_msg:
                bot.edit_message_text(error_msg,
                                      call.message.chat.id, call.message.message_id)
            else:
                bot.edit_message_text("Привычки на сегодня:",
                                      call.message.chat.id, call.message.message_id,
                                      reply_markup=keyboard)
        else:
            bot.answer_callback_query(call.id, "Ошибка.")