#from storage_bot import*

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackContext, MessageHandler, Filters

REGISTRATION, NAME, ADDRESS, PHONE, EMAIL = range(5)



def start(update: Update, context) -> None:
    keyboard = [
        [InlineKeyboardButton("Узнать  подробнее", callback_data="open_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        '''Привет! 👋 Я телеграм-бот. 🤖\n
Наша компания предлагает услуги по хранению:\n
🚲 1. Сезонных вещей: снегоходов, лыж, сноубордов, велосипедов, самокатов;\n
🪑 2. Вещей во время переезда;\n
🏺 3. Памятных вещей, которые занимают много места дома, но ценны для хозяев.''',
        reply_markup=reply_markup
    )


def get_all_addresses():
    return [
        "📍 1. г. Москва, ул. Ленина, д. 10",
        "📍 2. г. Москва, пр. Мира, д. 25",
        "📍 3. г. Москва, ул. Тверская, д. 15",

    ]


def get_allowed_items():
    return """<b>Разрешенные для хранения вещи:</b>

✅ Сезонные транспортные средства:
- Велосипеды
- Самокаты
- Лыжи и сноуборды
- Снегоходы

✅ Мебель и предметы интерьера:
- Диваны, кресла
- Шкафы, комоды
- Столы, стулья

✅ Бытовая техника:
- Холодильники
- Стиральные машины
- Телевизоры

✅ Личные вещи:
- Одежда
- Книги
- Документы
- Спортивный инвентарь
"""


def get_prohibited_items():
    return """<b>Запрещенные для хранения вещи:</b>

❌ Опасные вещества:
- Взрывчатые материалы
- Легковоспламеняющиеся жидкости
- Яды и токсины

❌ Продукты питания:
- Скоропортящиеся продукты
- Алкогольные напитки
- Замороженные продукты

❌ Живые существа:
- Животные
- Растения

❌ Прочее:
- Деньги и ценные бумаги
- Оружие и боеприпасы
- Наркотические вещества
"""


def get_pricing_text():
    return """<b>Стоимость хранения</b>

📦 Малый бокс (3 м³) - 1,500 руб./мес
📦 Средний бокс (5 м³) - 3,500 руб./мес
📦 Большой бокс (10 м³) - 5,000 руб./мес

🚚 Доставка вещей на склад - бесплатно"""

def process_agreement_accept(update: Update, context: CallbackContext) -> int:

    query = update.callback_query
    query.answer()
    try:
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=context.user_data.get('agreement_message_id')
        )
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
    
    
    context.user_data['registration'] = {'user_id': query.from_user.id}

    context.bot.send_message(
        chat_id=query.message.chat_id,
        text="✅ Для завершения оформления введите ваши данные:\n\nВведите ваши <b>Фамилию, Имя и Отчество</b>:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_registration")]
        ])
    )
    return NAME


def process_agreement_decline(update: Update, context: CallbackContext) -> int:

    query = update.callback_query
    try:
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=context.user_data.get('agreement_message_id')
        )
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    context.bot.send_message(
        chat_id=query.message.chat_id,
        text="❌ Для оформления заказа необходимо ваше согласие на обработку персональных данных.\n\n"
             "Если вы передумаете, можете начать процесс заказа заново.",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="open_menu")],
            [InlineKeyboardButton("Попробовать снова", callback_data="order_box")]
        ])
    )
    return ConversationHandler.END

