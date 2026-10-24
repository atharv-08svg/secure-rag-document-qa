from database import SessionLocal
from models import Role

db = SessionLocal()

roles = db.query(Role).all()

for role in roles:
    print(f"\nRole: {role.name}")

    for permission in role.permissions:
        print(f"  - {permission.name}")

db.close()