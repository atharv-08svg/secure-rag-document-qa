
from database import engine, Base
from models import User, Role, Permission, Document

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")