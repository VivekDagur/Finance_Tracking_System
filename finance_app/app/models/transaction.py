from datetime import datetime, date

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..db import Base


class Transaction(Base):
    """
    Financial transaction belonging to a user.

    We index user_id, date, and category to make typical queries
    (per-user history, date ranges, and category breakdowns) efficient.
    Indexes improve query performance for filtering and summary operations.
    """

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # "income" or "expense"
    category = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    description = Column(String, nullable=True)
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    user = relationship("User", back_populates="transactions")

