import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

BACKEND_DIR = Path(__file__).resolve().parents[1]

TEST_DB_NAME = "community_test_db"
TEST_DATABASE_URL = (
    f"postgresql+psycopg2://user:password@localhost:5433/{TEST_DB_NAME}"
)

# Must happen before any `app.*` import so Settings picks it up.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402

ADMIN_ENGINE_URL = "postgresql+psycopg2://user:password@localhost:5433/postgres"

TRUNCATE_TABLES = """
TRUNCATE TABLE
    investor_request_status_history,
    investor_requests,
    conversation_speakers,
    conversations,
    users
RESTART IDENTITY CASCADE
"""


def _ensure_database_exists() -> None:
    engine = create_engine(ADMIN_ENGINE_URL, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": TEST_DB_NAME},
            ).scalar()
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    finally:
        engine.dispose()


_ensure_database_exists()

_migrations = AlembicConfig(str(BACKEND_DIR / "alembic.ini"))
_migrations.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
command.upgrade(_migrations, "head")


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_database():
    engine = create_engine(TEST_DATABASE_URL, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            connection.execute(text(TRUNCATE_TABLES))
    finally:
        engine.dispose()
    yield


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


def register_user(
    client: TestClient,
    *,
    email: str | None = None,
    password: str = "StrongPass@123",
    full_name: str = "Test Person",
) -> dict:
    payload = {
        "full_name": full_name,
        "email": email or unique_email(),
        "password": password,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, email: str, password: str = "StrongPass@123") -> dict:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def user(client: TestClient) -> dict:
    return register_user(client)


@pytest.fixture()
def user_token(client: TestClient, user: dict) -> str:
    return login(client, user["email"])["access_token"]


@pytest.fixture()
def admin(db) -> dict:
    email = unique_email("admin")
    admin_user = User(
        full_name="Seed Admin",
        email=email,
        password_hash=hash_password("AdminPass@123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return {
        "id": str(admin_user.id),
        "full_name": admin_user.full_name,
        "email": admin_user.email,
        "role": admin_user.role.value,
    }


@pytest.fixture()
def admin_token(client: TestClient, admin: dict) -> str:
    return login(client, admin["email"], "AdminPass@123")["access_token"]
