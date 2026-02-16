from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import License

app = FastAPI(title="License Server")
init_db()  # создаст таблицы, если их ещё нет

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ActivateRequest(BaseModel):
    hwid: str
    license_key: str

class ActivateResponse(BaseModel):
    success: bool
    message: str
    expiry_date: datetime | None = None

class CheckRequest(BaseModel):
    hwid: str

class CheckResponse(BaseModel):
    success: bool
    is_active: bool
    expiry_date: datetime | None = None
    message: str = ""

@app.get("/")
def root():
    return {"message": "License Server is running"}

@app.post("/activate", response_model=ActivateResponse)
def activate(req: ActivateRequest, db: Session = Depends(get_db)):
    lic = db.query(License).filter(License.license_key == req.license_key).first()
    if not lic:
        raise HTTPException(status_code=404, detail="Лицензионный ключ не найден")
    
    # Проверяем, не занят ли этот HWID другим активным ключом
    existing = db.query(License).filter(License.hwid == req.hwid).first()
    if existing and existing.id != lic.id and existing.is_active and existing.expiry_date and existing.expiry_date > datetime.utcnow():
        raise HTTPException(status_code=400, detail="Этот компьютер уже активирован другим ключом")
    
    # Если ключ уже привязан к другому HWID и тот активен — отказ
    if lic.hwid and lic.hwid != req.hwid:
        other = db.query(License).filter(License.hwid == lic.hwid).first()
        if other and other.is_active and other.expiry_date and other.expiry_date > datetime.utcnow():
            raise HTTPException(status_code=400, detail="Ключ уже используется на другом устройстве")
    
    # Если уже активен на этом же HWID и срок не истёк
    if lic.hwid == req.hwid and lic.expiry_date and lic.expiry_date > datetime.utcnow():
        return ActivateResponse(success=True, message="Лицензия уже активна", expiry_date=lic.expiry_date)
    
    # Активируем
    lic.hwid = req.hwid
    lic.expiry_date = datetime.utcnow() + timedelta(days=14)
    lic.is_active = True
    db.commit()
    
    return ActivateResponse(success=True, message="Лицензия активирована на 14 дней", expiry_date=lic.expiry_date)

@app.post("/check", response_model=CheckResponse)
def check(req: CheckRequest, db: Session = Depends(get_db)):
    lic = db.query(License).filter(License.hwid == req.hwid).first()
    if not lic:
        return CheckResponse(success=False, is_active=False, message="Лицензия не найдена")
    
    now = datetime.utcnow()
    is_active = lic.is_active and lic.expiry_date and lic.expiry_date > now
    
    return CheckResponse(
        success=True,
        is_active=is_active,
        expiry_date=lic.expiry_date,
        message="Активна" if is_active else "Истекла или деактивирована"
    )