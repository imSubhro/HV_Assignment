from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from tests.conftest import auth_header, login, register_user, unique_email


def test_register_returns_201_and_ignores_role_field(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Asha Verma",
            "email": "  Asha@Example.COM ",
            "password": "StrongPass@123",
            "role": "admin",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == "asha@example.com"
    assert body["role"] == "user"
    assert body["full_name"] == "Asha Verma"
    assert "password_hash" not in body
    assert "password" not in body
    assert body["id"]


def test_register_duplicate_email_returns_409_case_insensitive(client):
    register_user(client, email="dup@example.com")
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Someone Else",
            "email": "DUP@example.com",
            "password": "StrongPass@123",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def test_register_weak_password_returns_422_with_field_details(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Weak Password",
            "email": "weak@example.com",
            "password": "weakpass",
        },
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert any(detail["field"] == "password" for detail in error["details"])


def test_register_missing_digits_and_invalid_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"full_name": "No Digit", "email": "not-an-email", "password": "Abcdefg1"},
    )
    assert response.status_code == 422
    fields = {detail["field"] for detail in response.json()["error"]["details"]}
    assert "email" in fields


def test_login_wrong_password_and_unknown_email_share_generic_message(client):
    register_user(client, email="known@example.com", password="StrongPass@123")

    wrong_password = client.post(
        "/api/v1/auth/login",
        json={"email": "known@example.com", "password": "WrongPass@123"},
    )
    unknown_email = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "StrongPass@123"},
    )

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert (
        wrong_password.json()["error"]["message"]
        == unknown_email.json()["error"]["message"]
        == "Invalid email or password"
    )


def test_login_and_me_flow(client):
    user = register_user(client, email="me@example.com")
    token = login(client, "me@example.com")["access_token"]

    response = client.get("/api/v1/auth/me", headers=auth_header(token))
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user["id"]
    assert body["email"] == "me@example.com"
    assert body["role"] == "user"


def test_me_without_token_and_with_expired_token(client):
    user = register_user(client, email="expired@example.com")

    assert client.get("/api/v1/auth/me").status_code == 401

    expired = jwt.encode(
        {
            "sub": user["id"],
            "role": "user",
            "iat": int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()),
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    response = client.get("/api/v1/auth/me", headers=auth_header(expired))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_user_token_on_admin_route_returns_403(client, user_token):
    response = client.get(
        "/api/v1/admin/conversations", headers=auth_header(user_token)
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_login_with_token_payload_shape(client):
    register_user(client, email="shape@example.com")
    body = login(client, "shape@example.com")
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == settings.access_token_expire_minutes * 60
    assert body["user"]["email"] == "shape@example.com"
    assert body["user"]["role"] == "user"


def test_inactive_user_cannot_login(client, db):
    from app.models.user import User

    register_user(client, email="inactive@example.com")
    user = db.query(User).filter(User.email == "inactive@example.com").one()
    user.is_active = False
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "StrongPass@123"},
    )
    assert response.status_code == 401


def test_admin_can_change_roles_but_not_demote_self(client, db, admin, admin_token):
    target = register_user(client, email=unique_email("target"))
    regular = register_user(client, email=unique_email("regular"))

    response = client.patch(
        f"/api/v1/users/{target['id']}/role",
        json={"role": "admin"},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"

    demote_self = client.patch(
        f"/api/v1/users/{admin['id']}/role",
        json={"role": "user"},
        headers=auth_header(admin_token),
    )
    assert demote_self.status_code == 400
    assert demote_self.json()["error"]["code"] == "BAD_REQUEST"

    missing = client.patch(
        "/api/v1/users/00000000-0000-0000-0000-000000000000/role",
        json={"role": "admin"},
        headers=auth_header(admin_token),
    )
    assert missing.status_code == 404

    regular_token = login(client, regular["email"])["access_token"]
    as_user = client.patch(
        f"/api/v1/users/{regular['id']}/role",
        json={"role": "admin"},
        headers=auth_header(regular_token),
    )
    assert as_user.status_code == 403
