from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.core.errors import BadRequest, Conflict, NotFound, Unauthorized
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RoleUpdateRequest,
    TokenResponse,
    UserPublic,
)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
users_router = APIRouter(prefix="/users", tags=["Users"])


@auth_router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(payload: RegisterRequest, db: DbSession) -> User:
    email = payload.email.lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise Conflict(
            "An account with this email already exists",
            details=[{"field": "email", "issue": "Email is already registered"}],
        )

    user = User(
        full_name=payload.full_name,
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and obtain a JWT access token",
)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    invalid_credentials = Unauthorized(
        "Invalid email or password",
        details=[{"field": "email", "issue": "Invalid email or password"}],
    )

    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise invalid_credentials
    if not user.is_active:
        raise Unauthorized("This account has been deactivated")

    access_token, expires_in = create_access_token(
        user_id=str(user.id), role=user.role.value
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=user,
    )


@auth_router.get(
    "/me",
    response_model=UserPublic,
    summary="Get the authenticated user's profile",
)
def read_me(current_user: CurrentUser) -> User:
    return current_user


@users_router.patch(
    "/{user_id}/role",
    response_model=UserPublic,
    summary="Change a user's role (admin only)",
)
def update_user_role(
    user_id: UUID,
    payload: RoleUpdateRequest,
    db: DbSession,
    admin: AdminUser,
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFound("User not found")

    if payload.role == UserRole.USER and user.id == admin.id:
        raise BadRequest("Administrators cannot demote themselves")

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user
