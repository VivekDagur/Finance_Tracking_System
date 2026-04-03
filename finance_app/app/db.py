from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# For this small project we use a local SQLite file.
# In production we would typically switch this URL to PostgreSQL.
SQLALCHEMY_DATABASE_URL = "sqlite:///./finance.db"

# `check_same_thread=False` is required for SQLite when used with FastAPI's
# async request handling, because SQLAlchemy sessions run in threadpool workers.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session.

    Each request gets its own session which is closed after the request
    finishes to avoid connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

