
from auth import hash_password, verify_password


def test_correct_password_verifies():
    password = "TestPassword123!"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_wrong_password_fails():
    password = "TestPassword123!"
    hashed = hash_password(password)

    assert verify_password("WrongPassword456!", hashed) is False


def test_password_hash_is_not_plain_text():
    password = "TestPassword123!"
    hashed = hash_password(password)

    assert hashed != password