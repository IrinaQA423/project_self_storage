from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext


def init_order_data(context: CallbackContext):
    if 'orders' not in context.bot_data:
        context.bot_data['orders'] = {
            'new': [
                {'id': 1001, 'client': 'Иван Иванов', 'status': 'новый'},
                {'id': 1002, 'client': 'Петр Петров', 'status': 'новый'}
            ],
            'storage': [
                {'id': 1000, 'client': 'Сидор Сидоров', 'status': 'хранится'}
            ],
            'completed': [],
            'expired': []
        }


def get_order_details(order_id: int, order_data: dict) -> tuple:
    """Возвращает детали заказа и сформированное сообщение"""
    order_details = {
        "id": order_id,
        "client": order_data.get('client', 'Иван Иванов'),
        "phone": order_data.get('phone', '+79123456789'),
        "address": order_data.get('address', 'ул. Примерная, 123'),
        "warehouse": order_data.get('warehouse', 'Склад №1'),
        "box_size": order_data.get('box_size', 'Средний (5м³)'),
        "start_date": order_data.get('start_date', '2023-11-15'),
        "end_date": order_data.get('end_date', '2024-01-15'),
        "price": order_data.get('price', '5000 руб'),
        "status": order_data.get('status', 'новый'),
        "created_at": order_data.get('created_at', '2023-11-14 15:30')
    }

    message = (
        f"📄 Детали заказа #{order_id}\n\n"
        f"👤 Клиент: {order_details['client']}\n"
        f"📞 Телефон: {order_details['phone']}\n"
        f"🏠 Адрес: {order_details['address']}\n\n"
        f"🏭 Склад: {order_details['warehouse']}\n"
        f"📦 Размер бокса: {order_details['box_size']}\n\n"
        f"📅 Начало аренды: {order_details['start_date']}\n"
        f"⏳ Окончание аренды: {order_details['end_date']}\n\n"
        f"💰 Стоимость: {order_details['price']}\n"
        f"🔄 Статус: {order_details['status']}\n"
        f"📅 Дата создания: {order_details['created_at']}"
    )

    return order_details, message


def show_expired_orders(update: Update, context: CallbackContext):
    """Показывает просроченные заказы"""
    query = update.callback_query
    query.answer()

    init_order_data(context)
    expired_orders = context.bot_data['orders']['expired']

    if not expired_orders:
        query.edit_message_text(
            "⏱️ Просроченных заказов нет",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_orders")]])
        )
        return

    keyboard = []
    for order in expired_orders:
        keyboard.append(
            [InlineKeyboardButton(
                f"⏱️ Заказ #{order['id']}",
                callback_data=f"expired_detail_{order['id']}"
            )]
        )

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_orders")])

    query.edit_message_text(
        "⏱️ Просроченные заказы:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def mark_order_expired(update: Update, context: CallbackContext):
    """Помечает заказ как просроченный"""
    query = update.callback_query
    query.answer()
    order_id = int(query.data.split("_")[-1])

    init_order_data(context)
    orders = context.bot_data['orders']

    # Находим и перемещаем заказ
    order_to_move = None
    for i, order in enumerate(orders['storage']):
        if order['id'] == order_id:
            order_to_move = orders['storage'].pop(i)
            break

    if not order_to_move:
        query.edit_message_text(f"⚠️ Заказ #{order_id} не найден в хранящихся заказах")
        return

    # Обновляем статус и добавляем в просроченные
    order_to_move['status'] = 'просрочен'

    orders['expired'].append(order_to_move)

    # Сохраняем изменения
    context.bot_data['orders'] = orders

    keyboard = [
        [InlineKeyboardButton("📦 Заказы на хранении", callback_data="orders_storage")],
        [InlineKeyboardButton("⏱️ Просроченные заказы", callback_data="orders_expired")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_orders")]
    ]

    query.edit_message_text(
        f"⏱️ Заказ #{order_id} просрочен!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_expired_order_details(update: Update, context: CallbackContext):
    """Показывает детали просроченного заказа"""
    query = update.callback_query
    query.answer()

    order_id = int(query.data.split('_')[-1])

    # Получаем данные заказа
    expired_orders = context.bot_data.get('orders', {}).get('expired', [])
    order = next((o for o in expired_orders if o['id'] == order_id), None)

    if not order:
        query.edit_message_text(f"❌ Заказ #{order_id} не найден")
        return

    _, message = get_order_details(order_id, order)

    # Кнопки управления
    keyboard = [
        [InlineKeyboardButton("🗑 Удалить заказ", callback_data=f"delete_expired_{order_id}")],
        [InlineKeyboardButton("🔙 К списку просроченных", callback_data="orders_expired")]
    ]

    query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_new_orders(query, context: CallbackContext):
    """Показывает список новых заказов"""
    init_order_data(context)
    orders = context.bot_data['orders']['new']

    if not orders:
        query.edit_message_text(
            "Новых заказов нет",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_orders")]])
        )
        return

    keyboard = []
    for order in orders:
        keyboard.append(
            [InlineKeyboardButton(f"🆔 Заказ #{order['id']}", callback_data=f"order_detail_{order['id']}")]
        )

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_orders")])

    query.edit_message_text(
        "📋 Список новых заказов:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_order_details(update: Update, context: CallbackContext):
    """Показывает детали конкретного заказа"""
    query = update.callback_query
    query.answer()

    try:
        order_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        query.edit_message_text("⚠️ Неверный формат номера заказа")
        return

    init_order_data(context)
    orders_data = context.bot_data['orders']

    found_order = None
    order_category = None

    for category in ['new', 'storage', 'completed']:
        for order in orders_data[category]:
            if order['id'] == order_id:
                found_order = order
                order_category = category
                break
        if found_order:
            break

    if not found_order:
        query.edit_message_text("⚠️ Заказ не найден")
        return
    elif order_category == 'storage':
        keyboard = [
        [
            InlineKeyboardButton("✅ Завершить", callback_data=f"complete_order_{order_id}"),
            InlineKeyboardButton("⏱️ Просрочен", callback_data=f"expire_order_{order_id}")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="orders_storage")]
    ]

    _, message = get_order_details(order_id, found_order)

    keyboard = []
    if order_category == 'new':
        keyboard = [
        [
            InlineKeyboardButton("✅ На склад", callback_data=f"accept_order_{order_id}"),
            InlineKeyboardButton("❌ Отменить ", callback_data=f"cancel_order_{order_id}")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="orders_new")]
    ]

    elif order_category == 'storage':
        keyboard = [
            [
                InlineKeyboardButton("✅ Завершен", callback_data=f"complete_order_{order_id}"),
                InlineKeyboardButton("❌ Просрочен", callback_data=f"mark_expired_{order_id}")
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data="orders_storage")]
        ]
    elif order_category == 'completed':
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="orders_completed")]
        ]

    query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_completed_orders(update: Update, context: CallbackContext):
    """Показывает список выполненных заказов"""
    query = update.callback_query
    query.answer()

    init_order_data(context)
    orders = context.bot_data['orders']['completed']

    if not orders:
        query.edit_message_text(
            "✅ Выполненных заказов нет",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_orders")]])
        )
        return

    keyboard = []
    for order in orders:
        keyboard.append(
            [InlineKeyboardButton(
                f"✅ Заказ #{order['id']}",
                callback_data=f"order_detail_{order['id']}"
            )]
        )

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_orders")])

    query.edit_message_text(
        "✅ Выполненные заказы:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def accept_order(update: Update, context: CallbackContext):
    """Перемещает заказ в статус 'На хранении'"""
    query = update.callback_query
    query.answer()
    order_id = int(query.data.split("_")[-1])

    init_order_data(context)
    orders = context.bot_data['orders']

    order_to_move = None

    # Находим и перемещаем заказ
    for i, order in enumerate(orders['new']):
        if order['id'] == order_id:
            order_to_move = orders['new'].pop(i)

            break
    if not order_to_move:
        query.edit_message_text(f"⚠️ Заказ #{order_id} не найден в новых заказах")
        return

    # Обновляем статус и добавляем на хранение
    order_to_move['status'] = 'на хранении'
    orders['storage'].append(order_to_move)

    # Сохраняем изменения
    context.bot_data['orders'] = orders

    keyboard = [
        [InlineKeyboardButton("📦 Заказы на хранении", callback_data="orders_storage")],
        [InlineKeyboardButton("🆕 Новые заказы", callback_data="orders_new")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
    ]

    query.edit_message_text(
        f"✅ Заказ #{order_id} успешно перемещен на хранение!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def cancel_order(update: Update, context: CallbackContext):
    """Отменяет заказ"""
    query = update.callback_query
    query.answer()
    order_id = int(query.data.split("_")[-1])

    init_order_data(context)
    orders = context.bot_data['orders']

    # Удаляем заказ из новых
    orders['new'] = [order for order in orders['new'] if order['id'] != order_id]

    keyboard = [
        [InlineKeyboardButton("🆕 Новые заказы", callback_data="orders_new")],
        [InlineKeyboardButton("🔙 В меню", callback_data="admin_orders")]
    ]

    query.edit_message_text(
        f"❌ Заказ #{order_id} успешно отменен",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_storage_orders(query, context: CallbackContext):
    """Показывает заказы на хранении"""
    init_order_data(context)
    orders = context.bot_data['orders']['storage']

    if not orders:
        query.edit_message_text(
            "Заказов на хранении нет",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_orders")]])
        )
        return

    keyboard = []
    for order in orders:
        status_icon = "📦" if order['status'] == 'хранится' else "⏳"
        keyboard.append(
            [InlineKeyboardButton(
                f"📦 Заказ #{order['id']}",
                callback_data=f"order_detail_{order['id']}"
            )]
        )

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_orders")])

    query.edit_message_text(
        "📦 Заказы на хранении:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def complete_order(update: Update, context: CallbackContext):
    """Завершает заказ"""
    query = update.callback_query
    query.answer()
    order_id = int(query.data.split("_")[-1])

    init_order_data(context)
    orders = context.bot_data['orders']

    order_to_move = None

    # Находим и перемещаем заказ
    for i, order in enumerate(orders['storage']):
        if order['id'] == order_id:
            order_to_move = orders['storage'].pop(i)
            break

    if not order_to_move:
        query.edit_message_text(f"⚠️ Заказ #{order_id} не найден в хранящихся заказах")
        return

    # Обновляем статус и добавляем в завершенные
    order_to_move['status'] = 'завершен'
    orders['completed'].append(order_to_move)

    # Сохраняем изменения
    context.bot_data['orders'] = orders

    keyboard = [

        [InlineKeyboardButton("✅ Выполненные заказы", callback_data="orders_completed")],
        [InlineKeyboardButton("📦 Заказы на хранении", callback_data="orders_storage")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
    ]

    query.edit_message_text(
        f"✅ Заказ #{order_id} успешно завершен!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def delete_expired_order(update: Update, context: CallbackContext):
    """Удаляет просроченный заказ"""
    query = update.callback_query
    query.answer()

    order_id = int(query.data.split('_')[-1])

    if 'orders' not in context.bot_data:
        context.bot_data['orders'] = {'expired': []}

    # Удаляем заказ из списка
    context.bot_data['orders']['expired'] = [
        o for o in context.bot_data['orders']['expired']
        if o['id'] != order_id
    ]

    query.edit_message_text(
        f"✅ Просроченный заказ #{order_id} удалён",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 К списку просроченных", callback_data="orders_expired")]
        ])
    )
