import os
import jwt

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv


load_dotenv()


SECRET_KEY = os.getenv("JWT_SECRET_KEY")

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict):

    payload = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload["exp"] = expire

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


def decode_access_token(token: str):

    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )