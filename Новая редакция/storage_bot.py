from dateutil.relativedelta import relativedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup,  KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, ConversationHandler
from sqlalchemy.exc import SQLAlchemyError    
from button_callback import button_callback
from helpers import start, get_all_addresses, get_allowed_items, get_prohibited_items, get_pricing_text, process_agreement_accept, process_agreement_decline
from settings import load_config
from storage_db import *
from admin import admin_panel, admin_callback_handler, setup_admin_handlers


REGISTRATION, NAME, ADDRESS, PHONE, EMAIL = range(5)


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


def process_name(update: Update, context: CallbackContext) -> int:
    """Обрабатываем ввод ФИО"""
    
    name = update.message.text.strip()
    if not name:
        update.message.reply_text("❌ Имя не может быть пустым. Пожалуйста, введите ФИО:")
        return NAME
    if 'registration' not in context.user_data:
        context.user_data['registration'] = {}
    
    context.user_data['registration']['name'] = name
    print ("Сохранено  ФИО {name}")
    update.message.reply_text(
         "Введите ваш <b>Телефон</b> (в формате +79991234567):",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup([["❌ Отменить"]], one_time_keyboard=True)
    )
    return PHONE

def process_phone(update: Update, context: CallbackContext) -> int:
    """Обрабатываем ввод телефона"""
    phone = update.message.text.strip()
    if not phone.startswith('+') or not phone[1:].isdigit():
        update.message.reply_text("❌ Неверный формат телефона. Пожалуйста, введите телефон в формате +79991234567:")
        return PHONE
    
    context.user_data['registration']['phone'] = phone
    update.message.reply_text(
        "Введите ваш <b>Email</b>:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_registration")]
        ])
    )
    return EMAIL

def process_email(update: Update, context: CallbackContext) -> int:
    """Обрабатываем ввод email"""
    email = update.message.text.strip()
    if '@' not in email or '.' not in email.split('@')[-1]:
        update.message.reply_text("❌ Неверный формат email. Пожалуйста, введите корректный email:")
        return EMAIL
    
    context.user_data['registration']['email'] = email
    update.message.reply_text(
        "Последний шаг! Введите ваш <b>Адрес</b> (город, улица, дом, квартира):",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_registration")]
        ])
    )
    return ADDRESS

def process_address(update: Update, context: CallbackContext) -> int:
    """Обрабатываем ввод адреса и завершаем регистрацию"""
    address = update.message.text.strip()
    if not address:
        update.message.reply_text("❌ Адрес не может быть пустым. Пожалуйста, введите ваш адрес:")
        return ADDRESS
    
    # Сохраняем данные в контексте
    user_data = context.user_data['registration']
    user_data['address'] = address
    
    # Сохраняем в базу данных
    order_data = context.user_data.get('order_data', {})
    message = (
        "🎉 Регистрация успешно завершена! Ваш заказ оформлен.\n\n"
        f"<b>Проверьте ваши данные:</b>\n"
        f"Имя: {user_data.get('name', 'не указано')}\n"
        f"Телефон: {user_data.get('phone', 'не указан')}\n"
        f"Email: {user_data.get('email', 'не указан')}\n"
        f"Адрес: {user_data.get('address', 'не указан')}\n\n"
        f"<b>Детали заказа:</b>\n"
        f"Тип: {order_data.get('order_type', 'не указан')}\n"
        f"Размер бокса: {order_data.get('volume', 'не указан')}\n"
        f"Дата начала: {order_data.get('start_date', 'не указана')}\n"
        f"Продолжительность: {order_data.get('duration', 'не указана')} мес.\n"
        f"Итого к оплате: {order_data.get('total_price', 'не указана')}₽"
    )
    
    # Сохраняем в базу данных
    try:
        save_to_database(user_data)

        
        
        update.message.reply_text(
            text=message,
            parse_mode='HTML'
            
        )
        
    except Exception as e:
        print(f"Ошибка сохранения в БД: {e}")
        update.message.reply_text(
            "❌ Произошла ошибка при сохранении данных. Пожалуйста, попробуйте позже.",
            parse_mode='HTML'
        )
    
    return ConversationHandler.END

def save_to_database(user_data):
    """Сохраняет данные пользователя в базу данных"""
    from db_conf import db_session, User, Order, BocksVolume, Warehouse
    
    try:
        # Создаем пользователя
        user = User(
            tg_id=user_data.get('user_id'),
            name=user_data.get('name'),
            email=user_data.get('email'),
            phone=user_data.get('phone'),
            address=user_data.get('address'),
            consent_pd=True
        )
        db_session.add(user)
        
        # Создаем заказ с дефолтными значениями
        default_warehouse = db_session.query(Warehouse).first()
        default_volume = db_session.query(BocksVolume).first()
        
        order = Order(
            user_id=user_data.get('user_id'),
            taking_it_myself=False,
            calling_things=False,
            volume_id=default_volume.id if default_volume else 1,
            warehouse_id=default_warehouse.id if default_warehouse else 1,
            payment=False,
            rent_start=datetime.now().date(),
            rent_end=(datetime.now() + relativedelta(months=1)).date()
        )
        db_session.add(order)
        
        db_session.commit()
        
    except SQLAlchemyError as e:
        db_session.rollback()
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error: {str(e)}")

def setup_registration_handlers(dispatcher):
    """Обновленный ConversationHandler с новыми состояниями"""
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(process_agreement_accept, pattern='^accept_agreement$')],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, process_name)],
            PHONE: [MessageHandler(Filters.text & ~Filters.command, process_phone)],
            EMAIL: [MessageHandler(Filters.text & ~Filters.command, process_email)],
            ADDRESS: [MessageHandler(Filters.text & ~Filters.command, process_address)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_registration),
            CallbackQueryHandler(cancel_registration, pattern='^cancel_registration$'),
            MessageHandler(Filters.regex('^❌ Отменить$'), cancel_registration)  # Добавьте обработчик кнопки отмены
    ]
)     
        
    dispatcher.add_handler(conv_handler)

def cancel_registration(update: Update, context: CallbackContext) -> int:
    """Отмена процесса регистрации"""
    try:
        update.message.reply_text(
            "❌ Регистрация отменена.",
            reply_markup=ReplyKeyboardRemove()
        )
    except AttributeError:
        update.callback_query.edit_message_text("❌ Регистрация отменена.")
    
    context.user_data.clear()
    return ConversationHandler.END

def main() -> None:

    try:
        tg_token = load_config()
        updater = Updater(tg_token, use_context=True)
        dp = updater.dispatcher

        setup_registration_handlers(dp) 
        setup_admin_handlers(dp)
        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CallbackQueryHandler(button_callback))
         
        print("Бот запущен...")
        updater.start_polling()
        updater.idle()
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == '__main__':
    main()
