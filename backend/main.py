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

# --- ПРОДВИНУТАЯ БАЗА SOS-ТЕРАПИИ ---
SOS_RESPONSES = {
    "anxiety": [
        "Тревога — это шторм, но ты — скала. Давай подышим: вдох на 4 счета, задержка на 4, выдох на 8.",
        "Попробуй технику '5-4-3-2-1': назови 5 предметов вокруг, которые видишь прямо сейчас.",
        "Это состояние временно. Оно пройдет. Я рядом."
    ],
    "anger": [
        "Злость требует выхода. Попробуй сильно сжать кулаки на 5 секунд и резко расслабить их.",
        "Напиши здесь самое злое сообщение, выплесни всё. Я никому не расскажу.",
        "Сделай глубокий выдох. Ты сильнее своих эмоций."
    ],
    "sadness": [
        "Грустить — это нормально. Дай себе право на это чувство. Что именно тебя расстроило?",
        "Я слышу твою боль. Ты не один в этом состоянии.",
        "Маленький шаг: просто выпей стакан воды. Ты молодец, что зашел сюда."
    ],
    "default": [
        "Твои чувства важны. Пиши всё до последнего слова.",
        "Это останется здесь. Ты в безопасности.",
        "Выплесни это. Не держи в себе. Что еще у тебя на душе?",
        "Я слышу тебя. Хорошо, что ты здесь.",
        "Дыши. Ты сильнее, чем кажется."
    ]
}

# --- ПОЛНЫЙ ПУТЬ 21 ДНЯ ---
TASKS = {
    1: "День 1: Просто подыши. 5 минут тишины с закрытыми глазами.",
    2: "День 2: Напиши одну вещь, за которую ты благодарен себе сегодня.",
    3: "День 3: Отключи уведомления во всех соцсетях на 2 часа.",
    4: "День 4: Сделай легкую разминку или пройдись 15 минут.",
    5: "День 5: Письмо гнева. Напиши на бумаге всё, что бесит, и порви её.",
    6: "День 6: Выпей стакан воды медленно, чувствуя каждый глоток.",
    7: "День 7: Похвали себя вслух перед зеркалом. Это важно.",
    8: "День 8: Удали одну ненужную подписку или приложение.",
    9: "День 9: Послушай любимую песню с закрытыми глазами, не отвлекаясь.",
    10: "День 10: Сделай цифровой детокс на весь вечер.",
    11: "День 11: Запиши 3 своих маленьких успеха за эту неделю.",
    12: "День 12: Приготовь себе что-то вкусное и красиво оформи тарелку.",
    13: "День 13: Попробуй лечь спать на 30 минут раньше обычного.",
    14: "День 14: Вспомни человека, который тебе приятен, и просто пожелай ему добра про себя.",
    15: "День 15: День тишины. Попробуй 1 час не разговаривать и не переписываться.",
    16: "День 16: Сделай 3 глубоких вдоха каждый раз, когда заходишь в соцсети.",
    17: "День 17: Нарисуй свое настроение на листке бумаги, даже если это просто каракули.",
    18: "День 18: Оставь себе поддерживающую записку на видном месте.",
    19: "День 19: Проведи 15 минут без гаджетов сразу после пробуждения.",
    20: "День 20: Напиши план на завтра, включив туда 1 приятное дело для себя.",
    21: "День 21: Оглянись назад. Ты прошел большой путь. Ты крутой!"
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
        "backend_url": os.getenv("BACKEND_URL"),
        "bot_token_status": "configured" if os.getenv("TELEGRAM_BOT_TOKEN") else "missing"
    }

# --- УМНАЯ ЛОГИКА SOS ---
@app.post("/api/sos")
async def sos_logic(data: dict): 
    message = data.get("message", "").lower()
    
    # Анализ ключевых слов для выбора категории помощи
    if any(word in message for word in ["тревога", "страх", "боюсь", "паника", "трясет"]):
        category = "anxiety"
    elif any(word in message for word in ["злость", "бесит", "ненавижу", "раздражает", "убить"]):
        category = "anger"
    elif any(word in message for word in ["грустно", "одиноко", "боль", "плохо", "плачу"]):
        category = "sadness"
    else:
        category = "default"
        
    return {"reply": random.choice(SOS_RESPONSES[category])}

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