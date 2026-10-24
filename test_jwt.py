
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from jwt_helper import (
    SECRET_KEY,
    ALGORITHM,
    create_access_token,
    decode_access_token,
)


def test_access_token_contains_user_data():
    data = {"user_id": 1, "role": "user"}

    token = create_access_token(data)
    decoded = decode_access_token(token)

    assert decoded["user_id"] == 1
    assert decoded["role"] == "user"
    assert "exp" in decoded


def test_invalid_token_is_rejected():
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("this.is.not-a-valid-token")


def test_expired_token_is_rejected():
    expired_payload = {
        "user_id": 1,
        "role": "user",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }

    expired_token = jwt.encode(
        expired_payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)