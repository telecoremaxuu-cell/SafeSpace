from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import random
from . import models, database
models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()
@app.get('/')
def home(): return {'status': 'SafeSpace Active'}
@app.post('/api/sos')
async def sos(msg: dict): return {'reply': 'Я тебя слышу. Ты в безопасности.'}
