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