from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship

from database import Base


# Role ↔ Permission many-to-many relationship
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True)
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )

    users = relationship("User", back_populates="role")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    role_id = Column(Integer, ForeignKey("roles.id"))

    role = relationship("Role", back_populates="users")
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=True)
    uploaded_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )