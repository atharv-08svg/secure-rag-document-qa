from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
from security import get_current_user


def require_permission(permission_name: str):

    def permission_checker(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):

        user = db.query(User).filter(
            User.id == current_user["user_id"]
        ).first()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )

        user_permissions = [
            permission.name
            for permission in user.role.permissions
        ]

        if permission_name not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action"
            )

        return user

    return permission_checker