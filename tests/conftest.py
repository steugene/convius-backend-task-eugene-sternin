import asyncio
from typing import AsyncGenerator, Generator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from alembic.config import Config
from alembic import command

from app.core.config import settings
from app.db.session import Base, get_db, get_engine
from app.main import app
from app.models.models import User, Restaurant
from app.core.security import get_password_hash
from app.crud.crud_user import user
from app.schemas.user import UserCreate


def run_migrations():
    """Run database migrations."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine and run migrations."""
    engine = get_engine()
    run_migrations()  # Run migrations to create tables
    yield engine


@pytest.fixture(scope="function")
def db(engine):
    """Create a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db) -> Generator:
    """Create a test client with a fresh database session."""

    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db) -> User:
    """Create a test user."""
    user_in = UserCreate(
        email="test@example.com", password="testpassword123", full_name="Test User"
    )
    return user.create(db, obj_in=user_in)


@pytest.fixture(scope="function")
def test_user_token(client: TestClient, test_user: User) -> str:
    """Get a test user's access token."""
    login_data = {
        "username": test_user.email,
        "password": "testpassword123",
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    tokens = r.json()
    return tokens["access_token"]


@pytest.fixture(scope="function")
def authorized_client(client: TestClient, test_user_token: str) -> TestClient:
    """Create an authorized test client."""
    client.headers = {**client.headers, "Authorization": f"Bearer {test_user_token}"}
    return client


@pytest.fixture(scope="function")
def test_restaurant(db) -> Restaurant:
    """Create a test restaurant for testing."""
    restaurant = Restaurant(
        name="Test Restaurant", description="A test restaurant", address="123 Test St"
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


@pytest.fixture(scope="function")
def test_dates() -> tuple[date, date]:
    """Create test dates for voting."""
    today = date.today()
    return today, today + timedelta(days=1)
