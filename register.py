from database import SessionLocal
from models import User, Role
from auth import hash_password


db = SessionLocal()

# User details
username = "atharv"
email = "atharv@example.com"
password = "MySecret123"

# Find the "user" role
role = db.query(Role).filter(Role.name == "user").first()

# Hash the password
hashed_password = hash_password(password)

# Create user
new_user = User(
    username=username,
    email=email,
    password_hash=hashed_password,
    role_id=role.id
)

# Save user
db.add(new_user)
db.commit()

print("User registered successfully!")
print("Username:", new_user.username)
print("Role:", role.name)

db.close()