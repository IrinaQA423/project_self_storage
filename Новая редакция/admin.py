import os
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler, ConversationHandler

from orders import show_expired_orders, mark_order_expired, show_expired_order_details, show_new_orders, show_order_details, show_completed_orders, accept_order, cancel_order, show_storage_orders, complete_order, delete_expired_order
load_dotenv()

admin_ids = list(map(int, os.getenv('ADMIN_IDS').split(',')))


def is_admin(update: Update) -> bool:
    """Проверяет, является ли пользователь администратором"""
    user = update.effective_user
    return user and user.id in admin_ids


def admin_panel(update: Update, context: CallbackContext) -> None:
    """Главное меню админ-панели"""
    if not is_admin(update):
        update.message.reply_text("⛔️ Доступ запрещен!")
        return

    keyboard = [
        [InlineKeyboardButton("📊 Статистика по заказам", callback_data="admin_stats")],
        [InlineKeyboardButton("📦 Заказы", callback_data="admin_orders")]
    ]

    if update.callback_query:
        update.callback_query.edit_message_text(
            "Админ-панель:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.message.reply_text(
            "Админ-панель:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


def admin_callback_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик нажатий кнопок админ-панели"""
    query = update.callback_query
    query.answer()

    if not is_admin(update):
        query.edit_message_text("⛔️ Доступ запрещен!")
        return

    data = query.data

    if data.startswith("accept_order_"):
        accept_order(update, context)
    elif data.startswith("cancel_order_"):
        cancel_order(update, context)
    elif data == "admin_back":
        admin_panel(update, context)
    elif data == "admin_cancel":
        cancel(update, context)
    elif data == "admin_stats":
        show_statistics(query)
    elif data == "admin_orders":
        show_orders(query)
    elif data == "orders_new":
        show_new_orders(query, context)
    elif data == "orders_storage":
        show_storage_orders(query, context)
    elif data.startswith("order_detail_"):
        show_order_details(update, context)
    elif data == "orders_expired":
        show_expired_orders(update, context)
    elif data == "orders_completed":
        show_completed_orders(update, context)
    elif data.startswith("complete_order_"):
        complete_order(update, context)
    elif data.startswith("mark_expired_"):
        mark_order_expired(update, context)
    elif data.startswith("storage_detail_"):
        show_order_details(update, context)
    elif data.startswith("completed_detail_"):
        show_order_details(update, context)
    elif data.startswith("expired_detail_"):
        show_expired_order_details(update, context)
    elif data.startswith("delete_expired_"):
        delete_expired_order(update, context)
    elif data == "admin_completed_orders":
        show_completed_orders(update, context)
    elif data.startswith("delete_expired_"):
        delete_expired_order(update, context)


def show_statistics(query) -> None:
    """Отображает статистику по заказам"""
    keyboard = [
        [InlineKeyboardButton("📊 Заказы с рекламы", callback_data="ad_orders_stats")],
        [InlineKeyboardButton("📦 Все заказы", callback_data="all_orders_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
    ]
    stats = "📊 Статистика по заказам: \n\n"
    query.edit_message_text(stats, reply_markup=InlineKeyboardMarkup(keyboard))


def show_orders(query):
    """Показывает меню управления заказами"""
    keyboard = [
        [InlineKeyboardButton("🆕 Новые заказы", callback_data="orders_new")],
        [InlineKeyboardButton("📦 Заказы на хранении", callback_data="orders_storage")],
        [InlineKeyboardButton("✅ Выполненные заказы", callback_data="admin_completed_orders")],
        [InlineKeyboardButton("⏱️ Просроченные заказы", callback_data="orders_expired")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
    ]
    query.edit_message_text(
        "Выберите тип заказов:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def cancel(update: Update, context: CallbackContext) -> int:
    """Отменяет текущее действие"""
    if update.callback_query:
        update.callback_query.edit_message_text("❌ Действие отменено")
        admin_panel(update, context)
    return ConversationHandler.END


def setup_admin_handlers(dispatcher):
    """Настраивает обработчики для админ-панели"""
    dispatcher.add_handler(CommandHandler("admin", admin_panel))
    dispatcher.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(admin|orders|order_detail|storage_detail|accept_order|cancel_order|complete_order|completed_detail|expired_detail|complete_order|mark_expired|delete_expired)"))
