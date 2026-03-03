import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import random
from . import models, database

# Загружаем переменные из .env
load_dotenv()

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# РАЗРЕШАЕМ ДОСТУП ДЛЯ GITHUB PAGES
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SOS_PHRASES = [
    "Твои чувства важны. Пиши всё до последнего слова.",
    "Это останется здесь. Ты в безопасности.",
    "Выплесни это. Не держи в себе.",
    "Я слышу твою боль. Хорошо, что ты здесь."
]

@app.get("/")
def home(): 
    return {"status": "SafeSpace Active"}

# Эндпоинт, чтобы фронтенд узнавал актуальную ссылку
@app.get("/api/config")
def get_config():
    return {
        "webapp_url": os.getenv("WEBAPP_URL"),
        "bot_token": "set" if os.getenv("TELEGRAM_BOT_TOKEN") else "not_set"
    }

@app.post("/api/sos")
async def sos_logic(message: dict): 
    return {"reply": random.choice(SOS_PHRASES)}

@app.get("/api/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        user = models.User(id=user_id, current_day=1)
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"day": user.current_day}

# Эндпоинт для обновления прогресса (Путь 21 дня)
@app.post("/api/user/{user_id}/next-day")
def next_day(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and user.current_day < 21:
        user.current_day += 1
        db.commit()
    return {"day": user.current_day}
# Словарь заданий (пока на неделю, потом расширим до 21)
TASKS = {
    1: "День 1: Просто подыши. 5 минут тишины с закрытыми глазами.",
    2: "День 2: Напиши в заметках одну вещь, за которую ты благодарен себе сегодня.",
    3: "День 3: Отключи уведомления во всех соцсетях на 2 часа.",
    4: "День 4: Сделай легкую разминку или пройдись 15 минут.",
    5: "День 5: Письмо гнева. Напиши на бумаге всё, что бесит, и сожги (или порви).",
    6: "День 6: Выпей стакан воды медленно, чувствуя каждый глоток.",
    7: "День 7: Похвали себя вслух перед зеркалом. Это не странно, это важно."
}

@app.get("/api/task/{user_id}")
async def get_task(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        user = models.User(id=user_id, current_day=1)
        db.add(user); db.commit(); db.refresh(user)
    
    task_text = TASKS.get(user.current_day, "Поздравляю! Ты прошел весь путь.")
    return {"day": user.current_day, "task": task_text}

@app.post("/api/task/complete/{user_id}")
async def complete_task(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and user.current_day < 21:
        user.current_day += 1
        db.commit()
        return {"status": "success", "new_day": user.current_day}
    return {"status": "done"}