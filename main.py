from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import License

app = FastAPI(title="License Server")
init_db()

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

@app.post("/activate", response_model=ActivateResponse)
def activate(req: ActivateRequest, db: Session = Depends(get_db)):
    # 1. Ищем ключ в БД
    lic = db.query(License).filter(License.license_key == req.license_key).first()
    if not lic:
        raise HTTPException(status_code=404, detail="Лицензионный ключ не найден")
    
    # 2. Проверяем, не занят ли этот HWID другим активным ключом
    existing_hwid = db.query(License).filter(License.hwid == req.hwid).first()
    if existing_hwid and existing_hwid.id != lic.id:
        # Если HWID уже привязан к другому ключу и этот ключ активен
        if existing_hwid.is_active and existing_hwid.expiry_date and existing_hwid.expiry_date > datetime.utcnow():
            raise HTTPException(status_code=400, detail="Этот компьютер уже активирован другим ключом")
        else:
            # Если старая запись неактивна, можно её очистить (опционально)
            existing_hwid.hwid = None
            existing_hwid.expiry_date = None
            existing_hwid.is_active = False
    
    # 3. Если ключ уже привязан к другому HWID и тот HWID активен — отказ
    if lic.hwid and lic.hwid != req.hwid:
        # Проверим, активен ли ключ на другом устройстве
        other = db.query(License).filter(License.hwid == lic.hwid).first()
        if other and other.is_active and other.expiry_date and other.expiry_date > datetime.utcnow():
            raise HTTPException(status_code=400, detail="Ключ уже используется на другом устройстве")
        # Если старая привязка неактивна, разрешаем перепривязку
        lic.hwid = None  # сбросим
    
    # 4. Если ключ уже активирован на этом же HWID и срок не истёк — просто возвращаем успех
    if lic.hwid == req.hwid and lic.expiry_date and lic.expiry_date > datetime.utcnow():
        return ActivateResponse(success=True, message="Лицензия уже активна", expiry_date=lic.expiry_date)
    
    # 5. Активируем: привязываем HWID и ставим срок на 14 дней
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

@app.get("/")
def root():
    return {"message": "License Server is running"}