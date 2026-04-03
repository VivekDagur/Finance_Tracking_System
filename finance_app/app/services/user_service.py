from sqlalchemy.orm import Session

from ..core.security import get_password_hash
from ..models.user import User
from ..schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    existing = get_user_by_email(db, user_in.email)
    if existing:
        raise ValueError("Email already registered")

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role="viewer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

