from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import Forbidden, Unauthorized
from app.core.security import TokenError, decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole

# HTTPBearer gives Swagger UI a single "paste your token" field in the
# Authorize dialog (it sends `Authorization: Bearer <token>` for us).
# auto_error=False so a missing header becomes our 401 UNAUTHORIZED envelope
# instead of FastAPI's default 403.
bearer_scheme = HTTPBearer(scheme_name="Bearer", auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]


def get_current_user(
    db: DbSession, credentials: BearerCredentials
) -> User:
    if credentials is None or not credentials.credentials:
        raise Unauthorized("Missing authentication token")
    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError:
        raise Unauthorized("Invalid or expired authentication token")

    subject = payload.get("sub")
    if not subject:
        raise Unauthorized("Invalid or expired authentication token")

    try:
        user_id = UUID(str(subject))
    except ValueError:
        raise Unauthorized("Invalid or expired authentication token")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise Unauthorized("Invalid or expired authentication token")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != UserRole.ADMIN:
        raise Forbidden("Administrator privileges are required")
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]


__all__ = [
    "AdminUser",
    "BearerCredentials",
    "CurrentUser",
    "DbSession",
    "bearer_scheme",
    "get_current_user",
    "require_admin",
]
