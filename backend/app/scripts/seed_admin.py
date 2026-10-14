"""Create (or update) the first administrator from the .env credentials.

Usage:
    python -m app.scripts.seed_admin
"""

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole


def seed_admin() -> User:
    email = settings.admin_email.strip().lower()
    password = settings.admin_password

    if len(password) < 8:
        raise SystemExit("ADMIN_PASSWORD must be at least 8 characters long")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(
                full_name="Platform Admin",
                email=email,
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(user)
            action = "created"
        else:
            user.password_hash = hash_password(password)
            user.role = UserRole.ADMIN
            user.is_active = True
            action = "updated"

        db.commit()
        db.refresh(user)
        print(f"Admin {action}: {user.email} (id={user.id})")
        return user
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
