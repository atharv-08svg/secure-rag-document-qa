from database import SessionLocal
from models import Role, Permission

db = SessionLocal()

# Create permissions
read_documents = Permission(name="read_documents")
upload_documents = Permission(name="upload_documents")
delete_documents = Permission(name="delete_documents")
manage_users = Permission(name="manage_users")

# Create roles
admin = Role(name="admin")
user = Role(name="user")

# Give permissions to roles
admin.permissions = [
    read_documents,
    upload_documents,
    delete_documents,
    manage_users
]

user.permissions = [
    read_documents
]

# Add everything to database
db.add_all([
    admin,
    user
])

db.commit()

print("Roles and permissions added successfully!")

db.close()