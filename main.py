import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# ============================================
# НАСТРОЙКИ (встроены прямо в код)
# ============================================
BOT_TOKEN = "8910428468:AAErEJTLK8b2oF5gwW1wQlUuQfS2QHf4mZY"  # ← ВСТАВЬТЕ СЮДА СВОЙ ТОКЕН
WEBAPP_URL = "https://nagibator441.github.io/VeigatStore/"  # ← ВСТАВЬТЕ СЮДА ССЫЛКУ НА САЙТ
# ============================================

# Настройка логирования
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ХРАНИТЕЛЬ ЖИЗНИ (чтобы хостинг не усыплял бота) ---
app = Flask('')

@app.route('/')
def home():
    return "Veigat Store Bot is alive! "

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# -------------------------------------------------------

# Клавиатура с кнопкой Web App
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🛍️ Открыть магазин Veigat",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )],
        [InlineKeyboardButton(
            text="💬 Связаться с менеджером",
            url="https://t.me/nagibator_447"
        )]
    ])
    return keyboard

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"👋 Добро пожаловать в <b>Veigat Store</b>!\n\n"
        f"💎 Эксклюзивная одежда и редкие айтемы\n"
        f" AI-подбор вещей по вашему запросу\n"
        f"⚡ Быстрая связь с менеджером\n\n"
        f"Нажмите кнопку ниже, чтобы начать:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

async def main():
    keep_alive()
    print("✅ Бот запущен и работает 24/7!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())