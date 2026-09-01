from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.auth import TokenResponse, UserLogin, UserRead, UserRegister
from app.services.auth import (
    DuplicateEmailError,
    InvalidCredentialsError,
    authenticate_user,
    issue_token_for,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: DbSession) -> UserRead:
    try:
        return register_user(db, payload)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: DbSession) -> TokenResponse:
    try:
        user = authenticate_user(db, payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=issue_token_for(user))


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUser) -> UserRead:
    return current_user
