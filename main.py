import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from flask import Flask
from threading import Thread

# ============================================
# НАСТРОЙКИ
# ============================================
BOT_TOKEN = "8910428468:AAErEJTLK8b2oF5gwW1wQlUuQfS2QHf4mZY"
WEBAPP_URL = "https://nagibator441.github.io/VeigatStore/"
MANAGER_USERNAME = "nagibator_447"
# ============================================

# Настройка логирования
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ХРАНИТЕЛЬ ЖИЗНИ ---
app = Flask('')


@app.route('/')
def home():
    return "Veigat Store Bot is alive!"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


# -----------------------

# Машина состояний для оформления заказа
class OrderForm(StatesGroup):
    name = State()
    phone = State()
    address = State()


# База данных товаров (можно расширить)
PRODUCTS = {
    "hoodie_black": {"name": "Oversize Худи Blackout", "price": 4500, "sizes": ["S", "M", "L", "XL"]},
    "tshirt_white": {"name": "Футболка Minimal White", "price": 2500, "sizes": ["S", "M", "L", "XL"]},
    "cargo_pants": {"name": "Брюки Cargo Techwear", "price": 5500, "sizes": ["S", "M", "L", "XL"]},
    "jacket_limited": {"name": "Куртка Veigat Limited", "price": 12900, "sizes": ["M", "L", "XL"]},
}


# Клавиатура с кнопкой Web App
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart_view")],
        [InlineKeyboardButton(text="💬 Связаться с менеджером", url=f"https://t.me/{MANAGER_USERNAME}")],
    ])
    return keyboard


# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"👋 Добро пожаловать в <b>Veigat Store</b>!\n\n"
        f"💎 Эксклюзивная одежда и редкие айтемы\n"
        f"🤖 AI-подбор вещей по вашему запросу\n"
        f"🛒 Удобная корзина и оформление заказа\n\n"
        f"Нажмите кнопку ниже:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


# Просмотр корзины
def get_cart_keyboard():
    pass


@dp.callback_query(F.data == "cart_view")
async def view_cart(callback: types.CallbackQuery, state: FSMContext):
    cart = await state.get_data()

    if not cart:
        await callback.message.answer(
            "🛒 Ваша корзина пуста\n\n"
            "Добавьте товары через Web App или выберите ниже:",
            reply_markup=get_catalog_keyboard()
        )
    else:
        total = sum(item["price"] for item in cart.values())
        items_text = "\n".join([f"{item['name']} ({item['size']}) - {item['price']} ₽" for item in cart.values()])

        await callback.message.answer(
            f"🛒 <b>Ваша корзина:</b>\n\n"
            f"{items_text}\n\n"
            f"💰 <b>Итого: {total} ₽</b>\n\n"
            f"Для оформления нажмите 'Оформить заказ'",
            reply_markup=get_cart_keyboard(),
            parse_mode="HTML"
        )

    await callback.answer()


# Показ каталога
def get_catalog_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👕 Худи Blackout - 4500₽", callback_data="product_hoodie_black")],
        [InlineKeyboardButton(text="👕 Футболка White - 2500₽", callback_data="product_tshirt_white")],
        [InlineKeyboardButton(text="👖 Брюки Cargo - 5500₽", callback_data="product_cargo_pants")],
        [InlineKeyboardButton(text="🧥 Куртка Limited - 12900₽", callback_data="product_jacket_limited")],
    ])
    return keyboard


# Выбор товара
@dp.callback_query(F.data.startswith("product_"))
async def select_product(callback: types.CallbackQuery, state: FSMContext):
    product_key = callback.data.replace("product_", "")
    product = PRODUCTS.get(product_key)

    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=size, callback_data=f"size_{product_key}_{size}")]
        for size in product["sizes"]
    ])

    await callback.message.answer(
        f"👕 <b>{product['name']}</b>\n"
        f"💰 Цена: {product['price']} ₽\n\n"
        f"Выберите размер:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# Выбор размера и добавление в корзину
@dp.callback_query(F.data.startswith("size_"))
async def select_size(callback: types.CallbackQuery, state: FSMContext):
    _, product_key, size = callback.data.split("_")
    product = PRODUCTS.get(product_key)

    if not product:
        await callback.answer("Ошибка", show_alert=True)
        return

    # Получаем текущую корзину
    cart = await state.get_data()
    cart_key = f"{product_key}_{size}"

    if cart_key in cart:
        await callback.answer("Этот товар уже в корзине!", show_alert=True)
        return

    # Добавляем товар
    cart[cart_key] = {
        "name": product["name"],
        "price": product["price"],
        "size": size,
        "product_key": product_key
    }
    await state.update_data(cart)

    await callback.message.answer(
        f"✅ <b>{product['name']}</b> (размер {size}) добавлен в корзину!\n\n"
        f"💰 Цена: {product['price']} ₽",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Продолжить покупки", callback_data="catalog")],
            [InlineKeyboardButton(text="💳 Оформить заказ", callback_data="cart_checkout")],
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


# Начало оформления заказа
@dp.callback_query(F.data == "cart_checkout")
async def start_checkout(callback: types.CallbackQuery, state: FSMContext):
    cart = await state.get_data()

    if not cart:
        await callback.answer("Корзина пуста!", show_alert=True)
        return

    await callback.message.answer(
        "📝 <b>Оформление заказа</b>\n\n"
        "Введите ваше <b>имя</b>:",
        parse_mode="HTML"
    )
    await state.set_state(OrderForm.name)
    await callback.answer()


# Ввод имени
@dp.message(OrderForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "📱 Теперь введите ваш <b>номер телефона</b>:\n"
        "(или нажмите кнопку ниже)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 Отправить номер", request_contact=True)]
        ]),
        parse_mode="HTML"
    )
    await state.set_state(OrderForm.phone)


# Ввод телефона
@dp.message(OrderForm.phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await process_address(message, state)


@dp.message(OrderForm.phone)
async def process_phone_text(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await process_address(message, state)


async def process_address(message: types.Message, state: FSMContext):
    await message.answer(
        "📍 Введите <b>адрес доставки</b>:\n"
        "(город, улица, дом, квартира)",
        parse_mode="HTML"
    )
    await state.set_state(OrderForm.address)


# Финализация заказа
@dp.message(OrderForm.address)
async def process_address_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    name = data.get("name")
    phone = data.get("phone")
    address = message.text

    # Формируем заказ
    total = sum(item["price"] for item in cart.values())
    items_text = "\n".join([f"• {item['name']} ({item['size']}) - {item['price']} ₽" for item in cart.values()])

    order_text = (
        f"🛍️ <b>НОВЫЙ ЗАКАЗ</b>\n\n"
        f"👤 <b>Клиент:</b> {name}\n"
        f"📱 <b>Телефон:</b> {phone}\n"
        f"📍 <b>Адрес:</b> {address}\n\n"
        f"📦 <b>Товары:</b>\n"
        f"{items_text}\n\n"
        f"💰 <b>Итого: {total} ₽</b>"
    )

    # Отправляем менеджеру
    try:
        await bot.send_message(
            chat_id=MANAGER_USERNAME,  # Или ID менеджера
            text=order_text,
            parse_mode="HTML"
        )
    except:
        # Если не получается отправить по username, отправим в личку создателю
        pass

    # Отправляем подтверждение клиенту
    await message.answer(
        f"✅ <b>Заказ оформлен!</b>\n\n"
        f"{order_text}\n\n"
        f"📩 Менеджер свяжется с вами в ближайшее время!",
        parse_mode="HTML"
    )

    # Очищаем корзину
    await state.clear()


# Команда catalog
@dp.message(Command("catalog"))
async def cmd_catalog(message: types.Message):
    await message.answer(
        "📦 <b>Каталог товаров:</b>",
        reply_markup=get_catalog_keyboard(),
        parse_mode="HTML"
    )


# Команда help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        f"📞 <b>Связь с менеджером:</b>\n\n"
        f"👤 @{MANAGER_USERNAME}\n\n"
        f"💬 Напишите нам для консультации!",
        parse_mode="HTML"
    )


async def main():
    keep_alive()
    print("✅ Бот запущен и работает 24/7!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
