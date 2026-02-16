from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class License(Base):
    __tablename__ = 'licenses'
    
    id = Column(Integer, primary_key=True)
    hwid = Column(String, unique=True, nullable=True)
    license_key = Column(String, unique=True, nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    telegram_username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)