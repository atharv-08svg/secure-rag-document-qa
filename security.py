from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from jwt_helper import decode_access_token


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:

        payload = decode_access_token(token)

        return payload

    except Exception:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )