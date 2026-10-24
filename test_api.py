import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import app
from database import Base, get_db
from models import Role, Permission, User
from auth import hash_password
from datetime import datetime, timedelta, timezone
import jwt

from jwt_helper import SECRET_KEY, ALGORITHM
from models import Document


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        read = Permission(name="read_documents")
        upload = Permission(name="upload_documents")
        delete = Permission(name="delete_documents")

        user_role = Role(name="user", permissions=[read])
        admin_role = Role(
            name="admin",
            permissions=[read, upload, delete],
        )

        db.add_all([user_role, admin_role])
        db.flush()

        test_user = User(
            username="pytest_user",
            email="pytest_user@example.com",
            password_hash=hash_password("TestPassword123!"),
            role=user_role,
        )

        db.add(test_user)
        test_admin = User(
        username="pytest_admin",
        email="pytest_admin@example.com",
        password_hash=hash_password("TestAdminPassword123!"),
        role=admin_role,
        )
        db.add(test_admin)
        db.commit()

        yield db

    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()



@pytest.fixture
def client(test_db, monkeypatch):
    # Make /login use the same temporary database as our tests.
    test_session_local = sessionmaker(
        bind=test_db.get_bind(),
        autoflush=False,
        autocommit=False,
    )
    monkeypatch.setattr("app.SessionLocal", test_session_local)

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()




def get_test_token(client):
    response = client.post(
        "/login",
        json={
            "username": "pytest_user",
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    # Verify that the token returned by /login can be decoded.
    from jwt_helper import decode_access_token
    decoded = decode_access_token(token)
    assert decoded["user_id"] == 1

    return token
    app.dependency_overrides.clear()


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "RAG API",
    }


def test_home_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "RAG API is running"
    }


def test_login_rejects_unknown_user(client):
    response = client.post(
        "/login",
        json={
            "username": "pytest_unknown_user",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_protected_endpoint_rejects_missing_token(client):
    response = client.get("/protected")

    assert response.status_code in (401, 403)


def test_login_accepts_correct_credentials(client):
    response = client.post(
        "/login",
        json={
            "username": "pytest_user",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_rejects_wrong_password(client):
    response = client.post(
        "/login",
        json={
            "username": "pytest_user",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_user_cannot_delete_documents(client):
    token = get_test_token(client)

    response = client.delete(
        "/documents/999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_protected_endpoint_rejects_invalid_token(client):
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert response.status_code == 401


def test_protected_endpoint_rejects_expired_token(client):
    expired_token = jwt.encode(
        {
            "user_id": 1,
            "role": "user",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401


def test_user_can_list_documents(client):
    token = get_test_token(client)

    response = client.get(
        "/documents",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, f"Status: {response.status_code}, Body: {response.text}"
    assert isinstance(response.json(), list)


def test_missing_document_returns_404(client):
    token = get_test_token(client)

    response = client.get(
        "/documents/999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def get_admin_token(client):
    response = client.post(
        "/login",
        json={
            "username": "pytest_admin",
            "password": "TestAdminPassword123!",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_upload_rejects_invalid_file_type(client):
    token = get_admin_token(client)

    response = client.post(
        "/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.pdf", b"fake PDF content", "application/pdf")},
    )

    assert response.status_code == 400


def test_upload_rejects_empty_file(client):
    token = get_admin_token(client)

    response = client.post(
        "/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 400