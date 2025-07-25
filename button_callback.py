import os
import requests
from datetime import datetime, timedelta
import calendar
from io import BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from data_base.db_conf import BocksVolume
from helpers import get_all_addresses, get_allowed_items, get_prohibited_items, get_pricing_text, process_agreement_accept, process_agreement_decline

REGISTRATION, NAME, LAST_NAME, PATRONYMIC, ADDRESS, PHONE, EMAIL = range(7)


def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == "open_menu":
        menu_keyboard = [
            [InlineKeyboardButton("📋 Правила хранения вещей", callback_data="rules")],
            [InlineKeyboardButton("💵 Стоимость хранения", callback_data="pricing")],
            [InlineKeyboardButton("📦 Заказать бокс для хранения", callback_data="order_box")]
        ]

        query.edit_message_text(
            text="Выберите опцию:",
            reply_markup=InlineKeyboardMarkup(menu_keyboard)
        )
    elif query.data == "rules":
        rules_keyboard = [
            [InlineKeyboardButton("✅ Разрешенные вещи", callback_data="allowed_items")],
            [InlineKeyboardButton("❌ Запрещенные вещи", callback_data="prohibited_items")],
            [InlineKeyboardButton("🔙 Назад", callback_data="open_menu")]
        ]

        query.edit_message_text(
            text="Выберите категорию правил:",
            reply_markup=InlineKeyboardMarkup(rules_keyboard))

    elif query.data == "allowed_items":

        query.edit_message_text(
            text=get_allowed_items(),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад к правилам", callback_data="rules")]
            ]))

    elif query.data == "prohibited_items":

        query.edit_message_text(
            text=get_prohibited_items(),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад к правилам", callback_data="rules")]
            ]))
    elif query.data == "pricing":

        query.edit_message_text(
            text=get_pricing_text(),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад в меню", callback_data="open_menu")]
            ]))

    elif query.data == "order_box":

        order_keyboard = [
            [InlineKeyboardButton("🚚 Заказать доставку", callback_data="order_delivery")],
            [InlineKeyboardButton("🔄 Отвезу вещи сам", callback_data="self_pickup")]
        ]

        query.edit_message_text(
            text="Как хотите передать вещи на хранение?",
            reply_markup=InlineKeyboardMarkup(order_keyboard)
        )

    elif query.data == "self_pickup":  # Новый обработчик для самовывоза
        addresses = get_all_addresses()
        # Создаем кнопки для каждого адреса
        address_buttons = [
            [InlineKeyboardButton(address, callback_data=f"address_{i}")]
            for i, address in enumerate(addresses)
        ]

        address_buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="order_box")])
        query.edit_message_text(
            text="🏭 Выберите склад для самовывоза:",
            reply_markup=InlineKeyboardMarkup(address_buttons)
        )

    elif query.data.startswith("address_"):
        address_num = int(query.data.split("_")[1])
        addresses = get_all_addresses()
        selected_address = addresses[address_num]

        context.user_data['selected_address'] = selected_address
        volums = BocksVolume.get_all_bocks_volum()
        keyboard = []
        for i in volums:
            keyboard.append([InlineKeyboardButton(f"📦 {i.volume} м³", callback_data=f"size_{i.id}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад к складам", callback_data="self_pickup")])
        keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data="open_menu")])

        query.edit_message_text(
            text=f"📍 Вы выбрали склад:\n{selected_address}\n\n"
                 "📏 Теперь выберите размер бокса:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("size_"):  # Обработка выбора размера бокса
        size_mapping = {
            "size_small": ("Малый (3 м³)", 1500),
            "size_medium": ("Средний (5 м³)", 3500),
            "size_large": ("Большой (10 м³)", 5000)
        }

        selected_size, selected_price = size_mapping[query.data]
        selected_address = context.user_data.get('selected_address', 'не указан')

        # Сохраняем выбор
        context.user_data['selected_size'] = selected_size
        context.user_data['selected_price'] = selected_price

        # Создаем клавиатуру для выбора даты начала
        today = datetime.now()
        days_keyboard = []

        # Кнопки на 7 дней вперед
        for i in range(7):
            date = today + timedelta(days=i)
            days_keyboard.append(
                [InlineKeyboardButton(
                    f"{date.strftime('%d.%m.%Y')} ({calendar.day_name[date.weekday()]})",
                    callback_data=f"start_date_{date.strftime('%Y-%m-%d')}"
                )]
            )

        days_keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"address_{list(get_all_addresses()).index(selected_address)}")])

        query.edit_message_text(
            text=f"📝 Ваш выбор:\n\n"
                 f"🏭 Склад: {selected_address}\n"
                 f"📦 Размер бокса: {selected_size}\n"
                 f"💳 Стоимость: {selected_price} руб/мес\n\n"
                 "📅 Выберите дату начала аренды:",
            reply_markup=InlineKeyboardMarkup(days_keyboard)
        )

    elif query.data.startswith("start_date_"):  # Обработка выбора даты начала
        start_date = query.data.split("_")[2]
        context.user_data['start_date'] = start_date

        # Преобразуем строку в дату
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")

        # Создаем клавиатуру для выбора продолжительности
        duration_keyboard = [
            [InlineKeyboardButton("1 месяц", callback_data="duration_1")],
            [InlineKeyboardButton("3 месяца", callback_data="duration_3")],
            [InlineKeyboardButton("6 месяцев", callback_data="duration_6")],
            [InlineKeyboardButton("12 месяцев", callback_data="duration_12")],
            [InlineKeyboardButton("🔙 Назад", callback_data=f"size_{context.user_data['selected_size'].split()[0].lower()}")]
        ]

        query.edit_message_text(
            text=f"📅 Начало аренды: {start_date_obj.strftime('%d.%m.%Y')}\n\n"
                 "⏳ Выберите продолжительность аренды:",
            reply_markup=InlineKeyboardMarkup(duration_keyboard)
        )

    elif query.data.startswith("duration_"):
        months = int(query.data.split("_")[1])
        context.user_data['duration_months'] = months

        # Рассчитываем итоговую стоимость
        price_per_month = context.user_data['selected_price']
        total_price = price_per_month * months

        # Рассчитываем дату окончания
        start_date = datetime.strptime(context.user_data['start_date'], "%Y-%m-%d")
        end_date = start_date + timedelta(days=30*months)

        # Сохраняем данные
        context.user_data['total_price'] = total_price
        context.user_data['end_date'] = end_date.strftime('%Y-%m-%d')

        confirmation_text = f"""
📋 <b>Подтвердите заказ:</b>

🏭 Склад: {context.user_data['selected_address']}
📦 Размер бокса: {context.
user_data['selected_size']}
📅 Начало аренды: {start_date.strftime('%d.%m.%Y')}
⏳ Окончание аренды: {end_date.strftime('%d.%m.%Y')}
💰 Стоимость: {total_price:.0f} руб (за {months} мес.)

"""
        confirmation_keyboard = [
            [InlineKeyboardButton("✅ Подтвердить заказ", callback_data="confirm_order")],
            [InlineKeyboardButton("🔄 Изменить параметры", callback_data="order_box")],
            [InlineKeyboardButton("🏠 В главное меню", callback_data="open_menu")]
        ]

        query.edit_message_text(
            text=confirmation_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(confirmation_keyboard)
        )

    elif query.data == "confirm_order":
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

    elif query.data == "accept_agreement":
        return process_agreement_accept(update, context)
        

    elif query.data == "decline_agreement":
        return process_agreement_decline(update, context)

    elif query.data == "order_delivery":
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
    elif query.data == "accept_agreement":
        return process_agreement_accept(update, context)

    elif query.data == "decline_agreement":
        return process_agreement_decline(update, context)
