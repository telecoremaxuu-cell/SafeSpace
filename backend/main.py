import os
import random
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, database

# Загружаем переменные окружения из .env
load_dotenv()

# Автоматическое создание таблиц при запуске
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="SafeSpace Pro Backend")

# НАСТРОЙКА CORS: Разрешаем доступ с GitHub Pages и локалки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# База фраз для SOS-терапии
SOS_PHRASES = [
    "Твои чувства важны. Пиши всё до последнего слова.",
    "Это останется здесь. Ты в безопасности.",
    "Выплесни это. Не держи в себе.",
    "Я слышу твою боль. Хорошо, что ты здесь.",
    "Дыши. Ты сильнее, чем кажется."
]

# Задания Пути 21 дня
TASKS = {
    1: "День 1: Просто подыши. 5 минут тишины с закрытыми глазами.",
    2: "День 2: Напиши в заметках одну вещь, за которую ты благодарен себе сегодня.",
    3: "День 3: Отключи уведомления во всех соцсетях на 2 часа.",
    4: "День 4: Сделай легкую разминку или пройдись 15 минут.",
    5: "День 5: Письмо гнева. Напиши на бумаге всё, что бесит, и сожги (или порви).",
    6: "День 6: Выпей стакан воды медленно, чувствуя каждый глоток.",
    7: "День 7: Похвали себя вслух перед зеркалом. Это не странно, это важно."
    # Сюда можно добавить остальные дни до 21
}

@app.get("/")
def home(): 
    return {"status": "SafeSpace Active", "version": "1.0.0"}

# --- СИСТЕМНЫЙ КОНФИГ ---
@app.get("/api/config")
def get_config():
    """Отдает фронтенду актуальные ссылки из .env"""
    return {
        "webapp_url": os.getenv("WEBAPP_URL"),
        "backend_url": os.getenv("BACKEND_URL"),  # Ссылка Ngrok для фронта
        "bot_token_status": "configured" if os.getenv("TELEGRAM_BOT_TOKEN") else "missing"
    }

# --- ЛОГИКА SOS ---
@app.post("/api/sos")
async def sos_logic(data: dict): 
    # message = data.get("message") # Можно сохранить в лог для анализа, если нужно
    return {"reply": random.choice(SOS_PHRASES)}

# --- ЛОГИКА ПОЛЬЗОВАТЕЛЯ И ЗАДАНИЙ ---
@app.get("/api/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        user = models.User(id=user_id, current_day=1)
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"day": user.current_day}

@app.get("/api/task/{user_id}")
async def get_task(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        user = models.User(id=user_id, current_day=1)
        db.add(user); db.commit(); db.refresh(user)
    
    task_text = TASKS.get(user.current_day, "Ты прошел основной путь! Продолжай заботиться о себе.")
    return {"day": user.current_day, "task": task_text}

@app.post("/api/task/complete/{user_id}")
async def complete_task(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and user.current_day < 21:
        user.current_day += 1
        db.commit()
        return {"status": "success", "new_day": user.current_day}
    return {"status": "already_done_or_max"}

# --- РАЗДЕЛ: АНОНИМНЫЙ ЧАТ ---
@app.get("/api/messages")
def get_chat_messages(db: Session = Depends(database.get_db)):
    """Получаем последние 50 сообщений для общего чата"""
    messages = db.query(models.Message).order_by(models.Message.timestamp.desc()).limit(50).all()
    # Возвращаем в хронологическом порядке (старые вверху)
    return [
        {
            "user_id": m.user_id, 
            "text": m.text, 
            "time": m.timestamp.strftime("%H:%M")
        } for m in reversed(messages)
    ]

@app.post("/api/messages/send")
async def send_chat_message(data: dict, db: Session = Depends(database.get_db)):
    """Сохраняем новое сообщение в базу"""
    u_id = data.get("user_id")
    text = data.get("text")
    
    if not text or not u_id:
        raise HTTPException(status_code=400, detail="Missing user_id or text")

    new_msg = models.Message(user_id=u_id, text=text)
    db.add(new_msg)
    db.commit()
    return {"status": "success"}