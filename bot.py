import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

# Берем данные из твоего .env
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Ссылка на твой фронтенд (GitHub Pages)
WEBAPP_URL = "https://твой-логин.github.io/SafeSpace/" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_command(message: types.Message):
    # Создаем кнопку для открытия Mini App
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
    print("Бот запущен и ждет нажатия /start...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())