from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, validator


class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0)
    type: str
    category: str
    date: date
    description: Optional[str] = None

    @validator("type")
    def validate_type(cls, v: str) -> str:
        if v not in {"income", "expense"}:
            raise ValueError('Transaction type must be either "income" or "expense"')
        return v


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[str] = None
    category: Optional[str] = None
    date: Optional[date] = None
    description: Optional[str] = None

    @validator("type")
    def validate_update_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in {"income", "expense"}:
            raise ValueError('Transaction type must be either "income" or "expense"')
        return v


class TransactionRead(TransactionBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class TransactionFilterParams(BaseModel):
    type: Optional[str] = None
    category: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)

    @validator("type")
    def validate_filter_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in {"income", "expense"}:
            raise ValueError('Filter type must be either "income" or "expense"')
        return v

    @validator("date_to")
    def validate_date_range(cls, v: Optional[date], values):
        date_from = values.get("date_from")
        if v is not None and date_from is not None and v < date_from:
            raise ValueError("End date must be on or after the start date")
        return v

