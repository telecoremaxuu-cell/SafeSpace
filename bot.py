import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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

async def send_daily_reminders():
    """Раз в сутки отправляет напоминание всем пользователям из базы."""
    db_path = 'safespace.db'
    if not os.path.exists(db_path):
        print("⚠️ БД не найдена, рассылка пропущена.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Получаем всех пользователей
        cursor.execute("SELECT id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f"Начинаю рассылку для {len(user_ids)} пользователей...")
        sent_count = 0
        for user_id in user_ids:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text="Как прошел твой день? Зайди в SafeSpace 🌿, чтобы поделиться мыслями или выполнить задание.",
                    # Добавляем кнопку для быстрого входа
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="Войти в SafeSpace", 
                            web_app=WebAppInfo(url=WEBAPP_URL)
                        )]
                    ])
                )
                sent_count += 1
                await asyncio.sleep(0.1) # Небольшая задержка, чтобы не спамить API Telegram
            except Exception as e:
                # Частая ошибка: бот заблокирован пользователем.
                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        print(f"Рассылка завершена. Отправлено {sent_count} сообщений.")
    except Exception as e:
        print(f"⚠️ Ошибка во время рассылки: {e}")

async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_daily_reminders, 'cron', hour=20) # Рассылка каждый день в 20:00
    scheduler.start()

    print("Бот ждет нажатия /start в Telegram...")
    print("Ежедневная рассылка запланирована.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())