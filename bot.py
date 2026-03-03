import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# 1. Загружаем переменные из .env
load_dotenv()

# 2. Берем данные (теперь строго из .env)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL") 

# Проверка для тебя (выведется в терминале при запуске)
if not WEBAPP_URL or "твой-логин" in WEBAPP_URL:
    print("⚠️ ОШИБКА: Проверь файл .env! Ссылка WEBAPP_URL либо пустая, либо содержит 'твой-логин'.")
else:
    print(f"✅ Бот запущен. Ссылка из .env: {WEBAPP_URL}")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_command(message: types.Message):
    # Создаем кнопку, которая берет адрес из переменной WEBAPP_URL
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Войти в SafeSpace 🌿", 
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ])
    
    await message.answer(
        f"Привет, {message.from_user.first_name}.\n\n"
        "Это твое безопасное пространство. Здесь тебя не осудят. "
        "Ты можешь выплеснуть всё, что накипело, или начать путь восстановления.\n\n"
        "Нажми на кнопку ниже, чтобы войти.",
        reply_markup=markup
    )

async def main():
    print("Бот ждет нажатия /start в Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())