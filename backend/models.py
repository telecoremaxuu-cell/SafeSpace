from sqlalchemy import Column, Integer, String
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True) # Это Telegram ID
    username = Column(String, nullable=True)
    current_day = Column(Integer, default=1) # Прогресс (от 1 до 21)