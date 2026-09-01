from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.schemas.auth import UserLogin, UserRegister


class DuplicateEmailError(Exception):
    """Raised when a user with the same email already exists."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials do not match a known user."""


def register_user(db: Session, data: UserRegister) -> User:
    user = User(email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateEmailError(f"Email '{data.email}' is already registered") from exc
    db.refresh(user)
    return user


def authenticate_user(db: Session, data: UserLogin) -> User:
    user = db.scalars(select(User).where(User.email == data.email)).first()
    if user is None or not verify_password(data.password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password")
    return user


def issue_token_for(user: User) -> str:
    return create_access_token(subject=str(user.id))
