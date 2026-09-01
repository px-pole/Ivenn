import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import InvalidTokenError, decode_access_token
from app.db.models import User
from app.db.session import get_db

DbSession = Annotated[Session, Depends(get_db)]

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> User:
    if not settings.require_authentication:
        user = db.query(User).first()
        if user is None:
            user = User(id=uuid.uuid4(), email="local@inventory-vault", password_hash="local-dev")
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
            except IntegrityError:
                db.rollback()
                user = db.query(User).filter(User.email == "local@inventory-vault").one()
        return user

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        subject = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.get(User, uuid.UUID(subject))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user


def require_same_user_scope(current_user: User, requested_user_id: uuid.UUID | None) -> uuid.UUID:
    if not settings.require_authentication:
        return requested_user_id or current_user.id
    if requested_user_id is not None and requested_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return requested_user_id or current_user.id


CurrentUser = Annotated[User, Depends(get_current_user)]
