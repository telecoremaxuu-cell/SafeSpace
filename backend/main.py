import os
import random
import asyncio
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, database
from .chat_manager import ConnectionManager

# Загружаем переменные окружения
load_dotenv()
from fastapi.responses import FileResponse

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

# --- MIDDLEWARE ДЛЯ МОНИТОРИНГА ОШИБОК ---
@app.middleware("http")
async def log_status_errors(request: Request, call_next):
    response = await call_next(request)
    if response.status_code >= 400:
        print(f"🚩 LOG MONITOR: Ошибка {response.status_code} на экране/пути: {request.url.path}")
    return response

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

manager = ConnectionManager()

# --- ЭНДПОИНТЫ ---
@app.get("/")
async def read_index():
    return FileResponse('frontend/index.html')

@app.get("/api/status")
def status(): 
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
        # Upsert: если пользователя нет, создаем его.
        user = models.User(id=user_id, current_day=1)
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"day": user.current_day}

@app.get("/api/task/{user_id}")
async def get_task(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        # Upsert: если пользователя нет, создаем его.
        user = models.User(id=user_id, current_day=1)
        db.add(user)
        db.commit()
        db.refresh(user)
    task = db.query(models.Task).filter(models.Task.day == user.current_day).first()
    task_text = task.text if task else "Путь завершен!"
    return {"day": user.current_day, "task": task_text}

@app.post("/api/task/complete/{user_id}")
async def complete_task(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        # Upsert: если юзер каким-то образом не создался, создаем и засчитываем 1-й день
        user = models.User(id=user_id, current_day=2) # Сразу ставим 2-й день
        db.add(user)
        db.commit()
    elif user.current_day < 21:
        user.current_day += 1
        db.commit()
    else: # Пользователь уже завершил все задания
        return {"status": "error"}
    
    # Получаем текст нового задания
    new_task = db.query(models.Task).filter(models.Task.day == user.current_day).first()
    new_task_text = new_task.text if new_task else "Все задания выполнены!"

    return {
        "status": "success", 
        "new_day": user.current_day,
        "task": new_task_text,
        "percentage": round((user.current_day / 21) * 100)
    }

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

# --- ЛОГИКА АНОНИМНОГО ЧАТА (ЭКРАН 4) ---

@app.post("/api/chat/report/{reporter_id}/{offender_id}")
async def report_user(reporter_id: int, offender_id: int):
    """Эндпоинт для жалобы на пользователя в приватном чате."""
    await send_admin_alert(f"Пользователь {reporter_id} пожаловался на пользователя {offender_id} в приватном чате.")
    return {"status": "report sent"}
    
@app.websocket("/ws/chat/{user_id}")
async def chat_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "message":
                text = data.get("text", "")
                if '<' in text or '>' in text or 'http' in text:
                    await websocket.send_json({"type": "sys_message", "text": "Ссылки и HTML-теги запрещены."})
                    continue
                await manager.broadcast(user_id, text)
    except WebSocketDisconnect:
        await manager.disconnect(user_id)