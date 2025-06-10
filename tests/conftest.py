import asyncio
import os
from datetime import date, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from alembic import command
from alembic.config import Config
from app.core.config import settings
from app.crud.crud_user import user
from app.db.session import get_db
from app.main import app
from app.models.models import Restaurant, User
from app.schemas.user import UserCreate


def get_test_database_url():
    """Get test database URL with proper credentials for local testing."""
    # Use postgres user for local testing if lunch_voting user doesn't exist
    test_user = os.getenv("TEST_POSTGRES_USER", "postgres")
    test_password = os.getenv("TEST_POSTGRES_PASSWORD", "")
    test_host = os.getenv("TEST_POSTGRES_HOST", "localhost")
    test_port = os.getenv("TEST_POSTGRES_PORT", "5432")
    test_db = os.getenv("TEST_POSTGRES_DB", "lunch_voting_test")

    return f"postgresql://{test_user}:{test_password}@{test_host}:{test_port}/{test_db}"


def run_migrations():
    """Run database migrations."""
    # Set environment variables that alembic will pick up
    test_user = os.getenv("TEST_POSTGRES_USER", "postgres")
    test_password = os.getenv("TEST_POSTGRES_PASSWORD", "")
    test_host = os.getenv("TEST_POSTGRES_HOST", "localhost")
    test_port = os.getenv("TEST_POSTGRES_PORT", "5432")
    test_db = os.getenv("TEST_POSTGRES_DB", "lunch_voting_test")

    # Temporarily override environment variables for alembic
    original_env = {}
    env_vars = {
        "POSTGRES_USER": test_user,
        "POSTGRES_PASSWORD": test_password,
        "POSTGRES_HOST": test_host,
        "POSTGRES_PORT": test_port,
        "POSTGRES_DB": test_db,
    }

    # Save original values and set test values
    for key, value in env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
    finally:
        # Restore original environment variables
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine and run migrations."""
    test_db_url = get_test_database_url()
    engine = create_engine(test_db_url)

    # Create test database if it doesn't exist
    db_name = test_db_url.split("/")[-1]
    base_url = test_db_url.rsplit("/", 1)[0] + "/postgres"
    temp_engine = create_engine(base_url, isolation_level="AUTOCOMMIT")

    with temp_engine.connect() as conn:
        try:
            conn.execute(text(f"CREATE DATABASE {db_name}"))
        except Exception:
            pass  # Database already exists

    temp_engine.dispose()

    # Run migrations on test database
    run_migrations()
    yield engine
    engine.dispose()


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
