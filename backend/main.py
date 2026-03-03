﻿import os
import random
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, database

# Загружаем переменные окружения
load_dotenv()

# Настройки бота для уведомлений
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Автоматическое создание таблиц
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="SafeSpace Pro Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

async def send_admin_alert(text: str):
    """Отправка уведомления админу в Telegram"""
    if BOT_TOKEN and ADMIN_ID:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json={"chat_id": ADMIN_ID, "text": f"🚨 ALERT: {text}"})
        except Exception as e:
            print(f"Ошибка отправки алерта: {e}")

def filter_bad_words(text: str):
    """Простейший фильтр мата (можно расширить список)"""
    bad_words = ["блять", "сука", "хуй", "пиздец", "ебать"] # Добавь свои
    for word in bad_words:
        if word in text.lower():
            text = text.lower().replace(word, "***")
    return text

# --- БАЗЫ ДАННЫХ КОНТЕНТА ---

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

TASKS = {
    1: "День 1: Ревизия чатов. Заглуши или покинь те чаты и каналы, которые вызывают у тебя негативные эмоции.",
    2: "День 2: Квадратное дыхание. 5 минут. Вдох (4с), задержка (4с), выдох (4с), задержка (4с). Это успокаивает нервную систему.",
    3: "День 3: Прогулка без цели. Выйди на улицу на 15 минут и просто иди, куда глаза глядят, не отвлекаясь на телефон.",
    4: "День 4: Благодарность. Запиши три вещи, за которые ты благодарен сегодняшнему дню. Неважно, насколько они малы.",
    5: "День 5: Письмо в никуда. Напиши на бумаге или здесь всё, что тебя злит или расстраивает. Потом удали или порви. Не держи в себе.",
    6: "День 6: Одна задача. Выбери одно дело, которое давно откладывал, и удели ему 25 минут, не отвлекаясь. Используй таймер.",
    7: "День 7: Цифровой детокс. Отложи телефон на час перед сном. Почитай книгу, послушай музыку или просто побудь в тишине.",
    8: "День 8: Контакт с природой. Найди дерево, цветок или просто посмотри на облака. Постарайся заметить 5 деталей.",
    9: "День 9: Комплимент себе. Подойди к зеркалу и скажи себе одну приятную вещь. Ты это заслужил.",
    10: "День 10: Слушай тело. Сделай небольшую разминку: потянись, разомни шею, плечи. Почувствуй, где есть напряжение и отпусти его.",
    11: "День 11: Момент осознанности. Во время простого действия (например, мытья посуды) сосредоточься на ощущениях: температура воды, запах мыла.",
    12: "День 12: Творческий импульс. Нарисуй что-нибудь, даже просто каракули. Или напиши пару строк стихотворения. Без цели и оценки.",
    13: "День 13: Доброе дело. Сделай что-то хорошее для другого человека, не ожидая ничего взамен. Даже мелочь имеет значение.",
    14: "День 14: Вспомни свой успех. Подумай о моменте, когда ты гордился собой. Проживи это чувство заново.",
    15: "День 15: День без новостей. Попробуй прожить один день, не читая новостные ленты. Защити свое информационное поле.",
    16: "День 16: Любимая песня. Включи трек, который поднимает тебе настроение, и просто послушай его от начала до конца, ничего не делая.",
    17: "День 17: Уборка пространства. Приберись на своем рабочем столе или в одной полке шкафа. Внешний порядок помогает внутреннему.",
    18: "День 18: План на завтра. Составь простой план на следующий день, включив в него одно дело 'для души'.",
    19: "День 19: Границы. Сегодня попробуй вежливо сказать 'нет' одной просьбе или предложению, которое тебе некомфортно.",
    20: "День 20: Мечта. Позволь себе 10 минут просто помечтать о чем-то приятном, не думая о том, 'реально' ли это.",
    21: "День 21: Подведение итогов. Ты прошел этот путь! Оглянись назад и похвали себя. Какой самый важный урок ты вынес для себя за эти 3 недели?"
}

# --- ЭНДПОИНТЫ ---

@app.get("/")
def home(): 
    return {"status": "SafeSpace Active", "version": "1.1.0"}

@app.get("/api/config")
def get_config():
    return {
        "webapp_url": os.getenv("WEBAPP_URL"),
        "backend_url": os.getenv("BACKEND_URL"),
        "admin_configured": bool(ADMIN_ID)
    }

@app.post("/api/sos")
async def sos_logic(data: dict): 
    message = data.get("message", "").lower()
    
    # Если в сообщении есть опасные слова — шлем алерт админу
    critical_words = ["конец", "умереть", "суицид", "помогите", "смерть"]
    if any(cw in message for cw in critical_words):
        await send_admin_alert(f"Критическое сообщение в SOS: {message}")

    if any(word in message for word in ["тревога", "страх", "боюсь", "паника", "трясет"]):
        category = "anxiety"
    elif any(word in message for word in ["злость", "бесит", "ненавижу", "раздражает", "убить"]):
        category = "anger"
    elif any(word in message for word in ["грустно", "одиноко", "боль", "плохо", "плачу"]):
        category = "sadness"
    else:
        category = "default"
        
    return {"reply": random.choice(SOS_RESPONSES[category])}

@app.get("/api/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        user = models.User(id=user_id, current_day=1)
        db.add(user); db.commit(); db.refresh(user)
    return {"day": user.current_day}

@app.get("/api/task/{user_id}")
async def get_task(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        user = models.User(id=user_id, current_day=1)
        db.add(user); db.commit(); db.refresh(user)
    task_text = TASKS.get(user.current_day, "Путь завершен!")
    return {"day": user.current_day, "task": task_text}

@app.post("/api/task/complete/{user_id}")
async def complete_task(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and user.current_day < 21:
        user.current_day += 1
        db.commit()
        return {"status": "success", "new_day": user.current_day}
    return {"status": "error"}

@app.get("/api/messages")
def get_chat_messages(db: Session = Depends(database.get_db)):
    messages = db.query(models.Message).order_by(models.Message.timestamp.desc()).limit(50).all()
    return [{"user_id": m.user_id, "text": m.text, "time": m.timestamp.strftime("%H:%M")} for m in reversed(messages)]

@app.post("/api/messages/send")
async def send_chat_message(data: dict, db: Session = Depends(database.get_db)):
    u_id = data.get("user_id")
    text = data.get("text", "")
    
    if not text or not u_id:
        raise HTTPException(status_code=400, detail="Missing data")

    # Фильтруем мат перед сохранением
    clean_text = filter_bad_words(text)
    
    # Если в чате жесть — уведомляем админа
    if "***" in clean_text:
        await send_admin_alert(f"Мат в чате от {u_id}: {text}")

    new_msg = models.Message(user_id=u_id, text=clean_text)
    db.add(new_msg); db.commit()
    return {"status": "success"}