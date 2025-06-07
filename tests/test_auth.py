from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.crud_user import user
from app.models.models import User
from app.schemas.user import UserCreate

def test_register_user(client: TestClient, db: Session) -> None:
    data = {
        "email": "newuser@example.com",
        "password": "newpassword",
        "full_name": "New User",
    }
    response = client.post(f"{settings.API_V1_STR}/auth/register", json=data)
    assert response.status_code == 200
    content = response.json()
    assert content["email"] == data["email"]
    assert content["full_name"] == data["full_name"]
    assert "id" in content
    assert "hashed_password" not in content

def test_register_existing_user(client: TestClient, test_user: User) -> None:
    data = {
        "email": test_user.email,
        "password": "newpassword",
        "full_name": "New User",
    }
    response = client.post(f"{settings.API_V1_STR}/auth/register", json=data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_success(client: TestClient, test_user: User) -> None:
    login_data = {
        "username": test_user.email,
        "password": "testpassword123",
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert response.status_code == 200
    content = response.json()
    assert "access_token" in content
    assert content["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient, test_user: User) -> None:
    login_data = {
        "username": test_user.email,
        "password": "wrongpassword",
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]

def test_login_nonexistent_user(client: TestClient) -> None:
    login_data = {
        "username": "nonexistent@example.com",
        "password": "password",
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]

def test_login_inactive_user(client: TestClient, db: Session) -> None:
    # Create inactive user
    user_in = UserCreate(
        email="inactive@example.com",
        password="password",
        full_name="Inactive User",
        is_active=False,
    )
    user_obj = user.create(db, obj_in=user_in)
    
    login_data = {
        "username": user_obj.email,
        "password": "password",
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert response.status_code == 400
    assert "Inactive user" in response.json()["detail"] 