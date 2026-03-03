from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from .database import Base
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    current_day = Column(Integer, default=1)
    last_active = Column(DateTime, default=datetime.utcnow)
