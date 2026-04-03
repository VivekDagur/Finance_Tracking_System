import logging
from datetime import timedelta

from sqlalchemy.orm import Session

from ..core.jwt import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from ..core.security import verify_password
from .user_service import get_user_by_email

logger = logging.getLogger(__name__)


def login_for_access_token(db: Session, email: str, password: str) -> str:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("Incorrect email or password")

    logger.info("User logged in successfully: user_id=%s email=%s", user.id, user.email)

    return create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

