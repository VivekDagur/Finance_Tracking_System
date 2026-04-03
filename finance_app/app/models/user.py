from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from ..db import Base


class User(Base):
    """
    User of the finance tracking system.

    Roles:
    - admin: full CRUD on all transactions
    - analyst: read/reporting only
    - viewer: read-only for own data
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="viewer", index=True)
    is_active = Column(Boolean, default=True)

    # Having an index on email makes lookups during login efficient.
    # Role is indexed so that future admin/reporting queries can filter users by role quickly.

    transactions = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
    )

