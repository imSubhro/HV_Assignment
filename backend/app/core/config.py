from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    app_name: str = "Community Platform API"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg2://user:password@localhost:5433/community_db"

    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Comma-separated in .env, e.g. "http://localhost:3000,http://localhost:5173".
    cors_origins: Annotated[list[str], NoDecode] = Field(default=["http://localhost:3000"])

    admin_email: str = "admin@example.com"
    admin_password: str = "ChangeMe@123"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("jwt_secret")
    @classmethod
    def secret_not_placeholder(cls, value: str) -> str:
        if value == "change-me-to-a-long-random-string":
            return value
        if len(value) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
