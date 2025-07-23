from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup,  KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, ConversationHandler

from button_callback import button_callback
from helpers import start, get_all_addresses, get_allowed_items, get_prohibited_items, get_pricing_text, process_agreement_accept, process_agreement_decline
from settings import load_config
from storage_db import save_user

REGISTRATION, NAME, LAST_NAME, PATRONYMIC, ADDRESS, PHONE, EMAIL = range(7)


def handle_contact_info(update: Update, context: CallbackContext) -> None:
    if 'expecting_contact' in context.user_data and context.user_data['expecting_contact']:
        context.user_data['contact_info'] = update.message.text

        try:

            pdf_url = os.getenv('PDF_URL')

            response = requests.get(pdf_url)
            response.raise_for_status()

            pdf_file = BytesIO(response.content)
            pdf_file.name = "соглашение_на_опд.pdf"

            sent_msg = context.bot.send_document(
                chat_id=query.message.chat_id,
                document=pdf_file,
                caption="📄 Пожалуйста, ознакомьтесь с соглашением на обработку персональных данных",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Я согласен", callback_data="accept_agreement")],
                    [InlineKeyboardButton("❌ Отказаться", callback_data="decline_agreement")]
                ])
            )
            context.user_data['agreement_message_id'] = sent_msg.message_id
        except Exception as e:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"⚠️ Ошибка при загрузке документа: {str(e)}"
            )
        context.user_data['expecting_contact'] = False


def registration_handler(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if not hasattr(context.user_data, 'reg_data'):
        context.user_data.reg_data = {}

    if 'step' not in context.user_data.reg_data:
        context.user_data.reg_data['name'] = text
        context.user_data.reg_data['step'] = 'last_name'
        update.message.reply_text("Введите вашу <b>Фамилию</b>:", parse_mode='HTML')
        return REGISTRATION

    elif context.user_data.reg_data['step'] == 'last_name':
        context.user_data.reg_data['last_name'] = text
        context.user_data.reg_data['step'] = 'patronymic'
        update.message.reply_text("Введите ваше <b>Отчество</b> (если нет - отправьте '-'):", parse_mode='HTML')
        return REGISTRATION

    elif context.user_data.reg_data['step'] == 'patronymic':
        context.user_data.reg_data['patronymic'] = text if text != '-' else None
        context.user_data.reg_data['step'] = 'address'
        update.message.reply_text("Введите ваш <b>Адрес</b>:", parse_mode='HTML')
        return REGISTRATION

    elif context.user_data.reg_data['step'] == 'address':
        context.user_data.reg_data['address'] = text
        context.user_data.reg_data['step'] = 'phone'
        reply_markup = ReplyKeyboardMarkup([[KeyboardButton("Отправить номер телефона",
            request_contact=True)]],
            resize_keyboard=True)
        update.message.reply_text("Введите ваш <b>Телефон</b> или нажмите кнопку ниже:",
            parse_mode='HTML',
            reply_markup=reply_markup)
        return REGISTRATION

    elif context.user_data.reg_data['step'] == 'phone':
        context.user_data.reg_data['phone'] = text
        context.user_data.reg_data['step'] = 'email'
        update.message.reply_text("Введите ваш <b>Email</b>:", parse_mode='HTML')
        return REGISTRATION

    elif context.user_data.reg_data['step'] == 'email':
        context.user_data.reg_data['email'] = text

        # Сохраняем все данные
        user_data = {
            **context.user_data.get('order_data', {}),
            **context.user_data.reg_data
        }
        save_user(user_data)

        update.message.reply_text(
            "✅ Регистрация завершена! Ваши данные:\n\n"
            f"Имя: {user_data['name']}\n"
            f"Фамилия: {user_data['last_name']}\n"
            f"Отчество: {user_data.get('patronymic', 'не указано')}\n"
            f"Адрес: {user_data['address']}\n"
            f"Телефон: {user_data['phone']}\n"
            f"Email: {user_data['email']}\n\n"
            "Спасибо за регистрацию!",
            reply_markup=ReplyKeyboardRemove()
        )

        return ConversationHandler.END


def main() -> None:

    try:
        tg_token = load_config()
        updater = Updater(tg_token, use_context=True)
        dp = updater.dispatcher

        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CallbackQueryHandler(button_callback))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_contact_info))
        print("Бот запущен...")
        updater.start_polling()
        updater.idle()
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == '__main__':
    main()
