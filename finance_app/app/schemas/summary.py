from pydantic import BaseModel


class CategorySummary(BaseModel):
    category: str
    total_income: float
    total_expense: float


class MonthlySummary(BaseModel):
    year: int
    month: int
    total_income: float
    total_expense: float


class FinancialSummary(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    category_breakdown: list[CategorySummary]
    monthly_summary: list[MonthlySummary]

