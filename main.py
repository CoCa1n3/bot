from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
import asyncio

# Хранение данных о заказах и корзине
user_data = {}

# Основные кнопки меню
main_menu_buttons = [
    ["Начать заказ", "О нас"],
    ["Мои заказы", "Оставить отзыв"],
    ["Настройки"]
]

# Функция для обработки команды /start
async def start(update: Update, context: CallbackContext):
    keyboard = ReplyKeyboardMarkup(main_menu_buttons, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать! Чем могу помочь?", reply_markup=keyboard)

# Обработка нажатия на кнопку "О нас"
async def about_us(update: Update, context: CallbackContext):
    await update.message.delete()
    await update.message.reply_text(
        "mubeens Нас выбирают из-за сытных и вкусных блюд, доступных цен и быстрой доставки.\n"
        "Служба доставки: +998777777777",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]])
    )

# Обработка нажатия на кнопку "Оставить отзыв"
async def leave_feedback(update: Update, context: CallbackContext):
    await update.message.delete()
    await update.message.reply_text(
        "Пожалуйста, оставьте отзыв здесь: https://t.me/umar_rakhmonberdievv",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]])
    )

# Обработка нажатия на кнопку "Мои заказы"
async def my_orders(update: Update, context: CallbackContext):
    await update.message.delete()
    user_id = update.message.from_user.id
    orders = user_data.get(user_id, {}).get('orders', [])
    if not orders:
        text = "У вас нет предыдущих заказов."
    else:
        text = "\n".join([f"Заказ {i+1}: {order}" for i, order in enumerate(orders)])
    
    await update.message.reply_text(
        f"Ваши заказы:\n{text}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]])
    )

# Обработка нажатия на кнопку "Настройки"
async def settings(update: Update, context: CallbackContext):
    await update.message.delete()
    user = update.message.from_user
    location = user_data.get(user.id, {}).get('location', 'Не указана')
    language = user.language_code
    await update.message.reply_text(
        f"Ваш номер: {user.id}\nВаш язык: {language}\nВаша локация: {location}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]])
    )

# Обработка нажатия на кнопку "Начать заказ"
async def start_order(update: Update, context: CallbackContext):
    await update.message.delete()
    keyboard = [
        [InlineKeyboardButton("Доставка", callback_data='delivery')],
        [InlineKeyboardButton("Самовывоз", callback_data='pickup')],
        [InlineKeyboardButton("Назад", callback_data='back')]
    ]
    await update.message.reply_text("Выберите способ получения заказа:", reply_markup=InlineKeyboardMarkup(keyboard))

# Обработка callback'ов для доставки и самовывоза
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == 'delivery':
        await query.message.delete()
        user_data[user_id] = {'location': None}
        await query.message.reply_text("Пожалуйста, отправьте свою локацию.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]]))
    elif query.data == 'pickup':
        await query.message.delete()
        await query.message.reply_text(
            "Самовывоз доступен по адресу: https://maps.app.goo.gl/ewNW19FvwrHXsbWSA",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]])
        )
    elif query.data == 'back':
        await query.message.delete()
        await start(query.message, context)

# Обработка получения локации
async def handle_location(update: Update, context: CallbackContext):
    await update.message.delete()
    user_id = update.message.from_user.id
    location = update.message.location
    user_data[user_id]['location'] = f"{location.latitude}, {location.longitude}"
    await update.message.reply_text(
        f"Ваш адрес: {user_data[user_id]['location']}. Подтвердить?", 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Да", callback_data='confirm_location')],
            [InlineKeyboardButton("Нет", callback_data='retry_location')],
            [InlineKeyboardButton("Назад", callback_data='back')]
        ])
    )

# Подтверждение локации или повторная отправка
async def confirm_location(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == 'confirm_location':
        await query.message.delete()
        await query.message.reply_text("Ваш адрес подтвержден.")
        await send_menu(query.message, context)
    elif query.data == 'retry_location':
        await query.message.delete()
        await query.message.reply_text("Пожалуйста, отправьте свою локацию заново.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]]))

# Отправка меню
async def send_menu(message, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Выгодные сеты", callback_data='sets')],
        [InlineKeyboardButton("Салаты", callback_data='salads')],
        [InlineKeyboardButton("Корзина", callback_data='basket')],
        [InlineKeyboardButton("Назад", callback_data='back')]
    ]
    await context.bot.send_photo(
        chat_id=message.chat.id, 
        photo=open('restaurant_photo.jpg', 'rb'),  # Замените на реальный путь к фотографии
        caption="Выберите категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Обработка выбора блюд
async def menu_button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.message.delete()

    if query.data == 'basket':
        await show_basket(query, context)
    else:
        await show_dishes(query, context, category=query.data)

# Функция показа блюд по категории
async def show_dishes(query: Update, context: CallbackContext, category: str):
    dishes = get_dishes_by_category(category)  # Функция для получения блюд по категории
    buttons = []
    
    for dish in dishes:
        buttons.append([InlineKeyboardButton(dish['name'], callback_data=f'dish_{dish["id"]}')])

    buttons.append([InlineKeyboardButton("Назад", callback_data='back')])
    await query.message.reply_text(f"Вы выбрали категорию: {category}. Выберите блюдо:", 
                                  reply_markup=InlineKeyboardMarkup(buttons))

# Функция показа блюда
async def dish_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.message.delete()
    dish_id = int(query.data.split('_')[1])
    dish = get_dish_by_id(dish_id)  # Функция для получения информации о блюде по ID
    
    buttons = [
        [
            InlineKeyboardButton("-", callback_data=f'decrease_{dish_id}'),
            InlineKeyboardButton("1", callback_data=f'quantity_{dish_id}'),
            InlineKeyboardButton("+", callback_data=f'increase_{dish_id}')
        ],
        [InlineKeyboardButton("Добавить в корзину", callback_data=f'add_to_basket_{dish_id}')],
        [InlineKeyboardButton("Назад", callback_data='back_to_menu')]
    ]
    
    await query.message.reply_photo(photo=open(dish['photo'], 'rb'),  # Замените на реальный путь к фотографии блюда
                                   caption=f"{dish['name']}\n{dish['description']}\nЦена: {dish['price']} сум",
                                   reply_markup=InlineKeyboardMarkup(buttons))

# Обработка изменения количества блюда
async def change_quantity(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.message.delete()
    dish_id = int(query.data.split('_')[1])
    user_id = query.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {'basket': {}}
    
    quantity = user_data[user_id]['basket'].get(dish_id, 1)
    
    if 'increase' in query.data:
        user_data[user_id]['basket'][dish_id] = quantity + 1
    elif 'decrease' in query.data and quantity > 1:
        user_data[user_id]['basket'][dish_id] = quantity - 1
    
    await dish_handler(update, context)

# Добавление блюда в корзину
async def add_to_basket(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.message.delete()
    dish_id = int(query.data.split('_')[3])
    user_id = query.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {'basket': {}}
    
    user_data[user_id]['basket'][dish_id] = user_data[user_id]['basket'].get(dish_id, 0) + 1
    
    await query.message.reply_text(f"Блюдо добавлено в корзину. Текущее количество: {user_data[user_id]['basket'][dish_id]}",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]]))

# Показ корзины
async def show_basket(update: Update, context: CallbackContext):
    user_id = update.from_user.id
    basket = user_data.get(user_id, {}).get('basket', {})
    if not basket:
        text = "Ваша корзина пуста."
    else:
        text = "\n".join([f"Блюдо {dish_id}: {quantity}" for dish_id, quantity in basket.items()])
    
    await update.message.reply_text(
        f"Ваша корзина:\n{text}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='back')]])
    )

def main():
    # Замените 'YOUR_BOT_TOKEN' на ваш реальный токен
    application = Application.builder().token('7370579930:AAG6JoGTvWlteNMnTgtadsjrtvcXHVjkQRo').build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    application.add_handler(CommandHandler('about_us', about_us))
    application.add_handler(CommandHandler('feedback', leave_feedback))
    application.add_handler(CommandHandler('my_orders', my_orders))
    application.add_handler(CommandHandler('settings', settings))
    application.add_handler(CommandHandler('start_order', start_order))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CallbackQueryHandler(menu_button_handler))
    application.add_handler(CallbackQueryHandler(dish_handler, pattern='^dish_'))
    application.add_handler(CallbackQueryHandler(change_quantity, pattern='^(increase|decrease)_'))
    application.add_handler(CallbackQueryHandler(add_to_basket, pattern='^add_to_basket_'))
    application.add_handler(CallbackQueryHandler(show_basket, pattern='^basket$'))

    asyncio.run(application.run_polling())

if __name__ == '__main__':
    main()
