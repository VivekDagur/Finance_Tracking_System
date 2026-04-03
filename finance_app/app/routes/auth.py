from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas.user import Token, UserCreate, UserRead
from ..services.auth_service import login_for_access_token
from ..services.user_service import create_user
from ..utils.responses import api_response


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    try:
        user = create_user(db, user_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return api_response(
        True,
        "User registered successfully",
        UserRead.model_validate(user).model_dump(),
    )


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    OAuth2-compatible login endpoint.

    - `username` field is used for email to match OAuth2PasswordRequestForm.
    """
    try:
        token = login_for_access_token(db, form_data.username, form_data.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return api_response(
        True,
        "Login successful",
        Token(access_token=token, token_type="bearer").model_dump(),
    )

