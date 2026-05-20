"""
Обработчики команд /start и /help.
"""

from api_client import api_request, user_tokens

def register_start(bot):
    """Регистрирует обработчики на объекте бота."""

    # ---------- Команда /start ----------
    @bot.message_handler(commands=['start'])
    def start_command(message):
        """
        Регистрирует пользователя в системе и сохраняет JWT-токен.
        Отправляет приветственное сообщение со списком команд.
        """
        # Извлекаем идентификатор пользователя Telegram и его username (может быть None)
        telegram_id = message.from_user.id
        username = message.from_user.username

        # Отправляем запрос на регистрацию/авторизацию в FastAPI
        # Если пользователь уже существует, вернётся тот же токен.
        resp = api_request(
            method="POST",
            endpoint="/auth/register",
            chat_id=message.chat.id,
            json_data={"telegram_id": telegram_id, "username": username}
        )

        if resp and "access_token" in resp:
            # Сохраняем токен в памяти для последующих запросов
            user_tokens[message.chat.id] = resp["access_token"]
            bot.reply_to(
                message,
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
            bot.reply_to(message, "Ошибка авторизации. Попробуйте позже.")

    # ---------- Команда /help ----------
    @bot.message_handler(commands=['help'])
    def help_command(message):
        """Отправляет справочное сообщение с описанием всех команд."""
        bot.send_message(
            message.chat.id,
            "📋 *Чат-бот трекинга привычек*\n\n"
            "• /habits — посмотреть список активных привычек\n"
            "• /add — добавить новую привычку\n"
            "• /edit — изменить название или описание привычки\n"
            "• /delete — удалить привычку\n"
            "• /daily — показать привычки на сегодня и отметить выполнение\n"
            "• /start — регистрация / авторизация\n\n"
            "🔔 Напоминание приходит ежедневно в 9:00.",
            parse_mode="Markdown"
        )