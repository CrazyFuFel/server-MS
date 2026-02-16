import sys
import secrets
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import License

# ====== ЗДЕСЬ ВСТАВЬТЕ ВАШУ СТРОКУ ПОДКЛЮЧЕНИЯ ИЗ SUPABASE ======
DATABASE_URL = "postgresql://postgres:alexeyalexey_625123@db.kyldvitxjytiaygbaphn.supabase.co:5432/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def generate_key():
    return secrets.token_hex(16)

def print_help():
    print("""
Команды:
  gen [username]          - Сгенерировать новый ключ (можно указать username)
  list                    - Показать все лицензии
  revoke <hwid_or_key>    - Деактивировать лицензию
  extend <hwid_or_key> <дней> - Продлить лицензию на N дней
  exit                    - Выход
""")

def main():
    session = SessionLocal()
    print("👑 Админ-панель лицензий")
    print_help()
    
    while True:
        try:
            cmd = input("> ").strip().split()
            if not cmd:
                continue
            if cmd[0] == "exit":
                break
            elif cmd[0] == "gen":
                username = cmd[1] if len(cmd) > 1 else None
                key = generate_key()
                lic = License(license_key=key, telegram_username=username)
                session.add(lic)
                session.commit()
                print(f"✅ Ключ создан: {key}")
            elif cmd[0] == "list":
                licenses = session.query(License).all()
                for lic in licenses:
                    now = datetime.utcnow()
                    status = "✅" if lic.is_active and lic.expiry_date and lic.expiry_date > now else "❌"
                    exp_str = lic.expiry_date.strftime("%Y-%m-%d %H:%M") if lic.expiry_date else "—"
                    print(f"{status} | Ключ: {lic.license_key} | HWID: {lic.hwid} | Истекает: {exp_str} | Юзер: {lic.telegram_username}")
            elif cmd[0] == "revoke":
                if len(cmd) < 2:
                    print("Использование: revoke <hwid_or_key>")
                    continue
                ident = cmd[1]
                lic = session.query(License).filter(
                    (License.hwid == ident) | (License.license_key == ident)
                ).first()
                if not lic:
                    print("❌ Не найдено")
                    continue
                lic.is_active = False
                session.commit()
                print(f"🔴 Лицензия отозвана для {ident}")
            elif cmd[0] == "extend":
                if len(cmd) < 3:
                    print("Использование: extend <hwid_or_key> <дней>")
                    continue
                ident = cmd[1]
                try:
                    days = int(cmd[2])
                except:
                    print("❌ Дни должны быть числом")
                    continue
                lic = session.query(License).filter(
                    (License.hwid == ident) | (License.license_key == ident)
                ).first()
                if not lic:
                    print("❌ Не найдено")
                    continue
                if lic.expiry_date:
                    lic.expiry_date += timedelta(days=days)
                else:
                    lic.expiry_date = datetime.utcnow() + timedelta(days=days)
                lic.is_active = True
                session.commit()
                print(f"🟢 Лицензия продлена до {lic.expiry_date.strftime('%Y-%m-%d %H:%M')}")
            else:
                print_help()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Ошибка: {e}")
    
    session.close()

if __name__ == "__main__":
    main()