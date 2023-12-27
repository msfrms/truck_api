import telebot
from app.config import settings

from auth.services.master_service import MasterService

from app.database import SessionLocal

import order.models

import chat.models

from validate_email import validate_email

bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN, parse_mode=None)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Я помогу вам отслеживать заявки для вашего региона",
    )
    bot.send_message(
        message.chat.id,
        "Как только поступит новая заявка в вашем регионе, я вам сообщу",
    )
    bot.send_message(message.chat.id, "Для начала работы, укажите вашу почту")


@bot.message_handler(content_types=["text"])
def get_text_messages(message):
    if validate_email(message.text):
        bot.send_message(
            message.chat.id,
            "Идет проверка почты, подождите немного",
        )
        email = message.text
        chat_id = message.chat.id

        db = SessionLocal()

        service = MasterService(db=db)
        is_updated_chat_id = service.update_chat_id(email=email, chat_id=chat_id)

        db.close()

        if is_updated_chat_id:
            bot.reply_to(
                message,
                "Почта успешно найдена, теперь вы получите уведомления о новых заявках",
            )
        else:
            bot.reply_to(
                message,
                f"Почта не найдена в нашей базе, возможно вы не зарегистрировались на сайте RideTS.ru или ввели почту неправильно\n"
                f"Если у вас возникли сложности то вы можете обратиться в техподдержку\n"
                f"по номеру телефона: +79950084323 или по e-mail: support@ridets.ru",
            )

    else:
        bot.reply_to(
            message,
            "Это не почта, возможно вы ошиблись, почта должа быть такой: example@example.com",
        )


bot.infinity_polling()
