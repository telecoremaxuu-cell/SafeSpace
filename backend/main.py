from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import random
from . import models, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# РАЗРЕШАЕМ ДОСТУП ДЛЯ GITHUB PAGES
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # В будущем заменим на твой github.io адрес
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SOS_PHRASES = ["Я тебя слышу.", "Ты в безопасности.", "Выплесни всё здесь."]

@app.get("/")
def home(): return {"status": "SafeSpace Active"}

@app.post("/api/sos")
async def sos_logic(message: dict): 
    return {"reply": random.choice(SOS_PHRASES)}

@app.get("/api/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        user = models.User(id=user_id, current_day=1)
        db.add(user); db.commit()
    return {"day": user.current_day}