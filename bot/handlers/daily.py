"""
Обработчики ежедневного трекинга:
- /daily – вывод списка привычек на сегодня с кнопками выполнения/невыполнения
- callback для отметки «выполнено»
- callback для отметки «не выполнено»
"""

from datetime import date
import telebot
from .api_client import api_request

def register_daily(bot):
    """Регистрирует обработчики ежедневного списка."""

    @bot.message_handler(commands=['daily'])
    def daily_habits(message):
        """
        Показывает список всех привычек на текущую дату.
        Для каждой привычки выводит две кнопки: отметить выполненной или невыполненной.
        """
        # Получаем сегодняшнюю дату в формате ISO (YYYY-MM-DD)
        today = date.today().isoformat()

        # Запрашиваем у API список записей DailyCompletion на сегодня
        resp = api_request("GET", "/habits/daily", message.chat.id,
                           params={"target_date": today})

        if resp is None:
            bot.send_message(message.chat.id, "Ошибка загрузки списка.")
            return
        if not resp:
            bot.send_message(message.chat.id, "На сегодня привычек нет.")
            return

        # Строим клавиатуру с двумя кнопками в ряд
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        for item in resp:
            # Если привычка уже выполнена, показываем ✅, иначе ⬜
            status = "✅" if item["completed"] else "⬜"
            habit_name = item['habit_name']
            habit_id = item['habit_id']

            # Кнопка "Выполнено"
            btn_done = telebot.types.InlineKeyboardButton(
                f"{status} {habit_name}",
                callback_data=f"complete_{habit_id}_{today}"
            )
            # Кнопка "Не выполнено"
            btn_fail = telebot.types.InlineKeyboardButton(
                "❌ Не выполнено",
                callback_data=f"fail_{habit_id}_{today}"
            )
            keyboard.add(btn_done, btn_fail)

        bot.send_message(message.chat.id, "Привычки на сегодня:",
                         reply_markup=keyboard)

    # ---------- Обработка нажатия «Выполнено» ----------
    @bot.callback_query_handler(func=lambda call: call.data.startswith("complete_"))
    def handle_complete(call):
        """
        Отмечает привычку выполненной.
        callback_data имеет формат: complete_<habit_id>_<date>
        """
        parts = call.data.split("_")
        if len(parts) != 3:
            return
        habit_id = parts[1]
        target_date = parts[2]

        # Отправляем запрос на эндпоинт /habits/daily/{habit_id}/complete
        resp = api_request(
            "POST",
            f"/habits/daily/{habit_id}/complete",
            call.message.chat.id,
            json_data={"date": target_date}
        )
        if resp:
            bot.answer_callback_query(call.id, "✅ Выполнено!")
            # Уведомляем, что список обновлён, но не перестраиваем клавиатуру,
            # чтобы не усложнять: пользователь может снова нажать /daily.
            bot.edit_message_text(
                "Список обновлён. Нажмите /daily для просмотра.",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, "Ошибка при отметке.")

    # ---------- Обработка нажатия «Не выполнено» ----------
    @bot.callback_query_handler(func=lambda call: call.data.startswith("fail_"))
    def handle_fail(call):
        """
        Отмечает привычку как невыполненную.
        callback_data имеет формат: fail_<habit_id>_<date>
        """
        parts = call.data.split("_")
        if len(parts) != 3:
            return
        habit_id = parts[1]
        target_date = parts[2]

        # Отправляем запрос на эндпоинт /habits/daily/{habit_id}/fail
        resp = api_request(
            "POST",
            f"/habits/daily/{habit_id}/fail",
            call.message.chat.id,
            json_data={"date": target_date}
        )
        if resp:
            bot.answer_callback_query(call.id, "❌ Отмечено как не выполнено.")
            bot.edit_message_text(
                "Список обновлён. /daily",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, "Ошибка.")