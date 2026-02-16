from sqlalchemy import Column, Integer, String, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class License(Base):
    __tablename__ = 'licenses'
    
    id = Column(Integer, primary_key=True)
    hwid = Column(String, unique=True, nullable=True)           # HWID устройства
    license_key = Column(String, unique=True, nullable=False)  # Уникальный ключ
    expiry_date = Column(DateTime, nullable=True)              # Дата истечения
    is_active = Column(Boolean, default=True)                  # Активна ли
    telegram_username = Column(String, nullable=True)          # Для удобства админа
    created_at = Column(DateTime, default=datetime.utcnow)     # Дата создания