import re
from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.models.user import UserRole

_PASSWORD_COMPLEXITY = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$")


class RegisterRequest(BaseModel):
    """Any `role` sent by the client is ignored - registration always creates a `user`."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "full_name": "Asha Verma",
                    "email": "asha@example.com",
                    "password": "StrongPass@123",
                }
            ]
        },
    )

    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not _PASSWORD_COMPLEXITY.match(value):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter and one digit"
            )
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {"email": "asha@example.com", "password": "StrongPass@123"}
            ]
        },
    )

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str
    role: UserRole
    created_at: datetime


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary


class RoleUpdateRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"role": "admin"}]})

    role: UserRole


__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "RoleUpdateRequest",
    "TokenResponse",
    "UserPublic",
    "UserSummary",
]
