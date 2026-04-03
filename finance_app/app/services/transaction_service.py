import logging
from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.dependencies import assert_owner_or_admin
from ..models.transaction import Transaction
from ..models.user import User
from ..schemas.summary import CategorySummary, FinancialSummary, MonthlySummary
from ..schemas.transaction import (
    TransactionCreate,
    TransactionFilterParams,
    TransactionUpdate,
)

logger = logging.getLogger(__name__)


def create_transaction(db: Session, current_user: User, tx_in: TransactionCreate) -> Transaction:
    # Database transactions ensure atomicity — either all changes succeed
    # or none are applied, preventing inconsistent state.
    tx = Transaction(
        user_id=current_user.id,
        amount=tx_in.amount,
        type=tx_in.type,
        category=tx_in.category,
        date=tx_in.date,
        description=tx_in.description,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    logger.info("Transaction created: transaction_id=%s user_id=%s", tx.id, current_user.id)
    return tx


def _base_query_for_user(db: Session, current_user: User):
    query = db.query(Transaction)
    if current_user.role != "admin":
        query = query.filter(Transaction.user_id == current_user.id)
    return query


def get_transactions(db: Session, current_user: User, filters: TransactionFilterParams) -> list[Transaction]:
    query = _base_query_for_user(db, current_user)
    if filters.type:
        query = query.filter(Transaction.type == filters.type)
    if filters.category:
        query = query.filter(Transaction.category == filters.category)
    if filters.date_from:
        query = query.filter(Transaction.date >= filters.date_from)
    if filters.date_to:
        query = query.filter(Transaction.date <= filters.date_to)

    return query.order_by(Transaction.date.desc()).offset(filters.offset).limit(filters.limit).all()


def get_transaction_by_id(db: Session, current_user: User, tx_id: int) -> Transaction | None:
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        return None
    assert_owner_or_admin(current_user, tx.user_id)
    return tx


def update_transaction(db: Session, current_user: User, tx_id: int, tx_in: TransactionUpdate) -> Transaction | None:
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        return None
    assert_owner_or_admin(current_user, tx.user_id)

    for field, value in tx_in.model_dump(exclude_unset=True).items():
        setattr(tx, field, value)

    # Database transactions ensure atomicity — either all changes succeed
    # or none are applied, preventing inconsistent state.
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def delete_transaction(db: Session, current_user: User, tx_id: int) -> bool:
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        return False
    assert_owner_or_admin(current_user, tx.user_id)

    # Database transactions ensure atomicity — either all changes succeed
    # or none are applied, preventing inconsistent state.
    db.delete(tx)
    db.commit()
    logger.info("Transaction deleted: transaction_id=%s user_id=%s", tx.id, current_user.id)
    return True


def compute_summary(db: Session, current_user: User, filters: TransactionFilterParams) -> FinancialSummary:
    # Derived values like balance are not stored to avoid inconsistency and race conditions.
    base_query = _base_query_for_user(db, current_user)
    if filters.type:
        base_query = base_query.filter(Transaction.type == filters.type)
    if filters.category:
        base_query = base_query.filter(Transaction.category == filters.category)
    if filters.date_from:
        base_query = base_query.filter(Transaction.date >= filters.date_from)
    if filters.date_to:
        base_query = base_query.filter(Transaction.date <= filters.date_to)

    income_sum = (
        base_query.filter(Transaction.type == "income")
        .with_entities(func.coalesce(func.sum(Transaction.amount), 0.0))
        .scalar()
    )
    expense_sum = (
        base_query.filter(Transaction.type == "expense")
        .with_entities(func.coalesce(func.sum(Transaction.amount), 0.0))
        .scalar()
    )

    category_rows = (
        base_query.with_entities(Transaction.category, Transaction.type, func.sum(Transaction.amount))
        .group_by(Transaction.category, Transaction.type)
        .all()
    )
    category_map = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for category, tx_type, total in category_rows:
        category_map[category][tx_type] += float(total or 0.0)
    category_breakdown = [
        CategorySummary(category=cat, total_income=vals["income"], total_expense=vals["expense"])
        for cat, vals in category_map.items()
    ]

    monthly_rows = (
        base_query.with_entities(
            func.strftime("%Y", Transaction.date),
            func.strftime("%m", Transaction.date),
            Transaction.type,
            func.sum(Transaction.amount),
        )
        .group_by(func.strftime("%Y", Transaction.date), func.strftime("%m", Transaction.date), Transaction.type)
        .all()
    )
    monthly_map = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for year_str, month_str, tx_type, total in monthly_rows:
        monthly_map[(int(year_str), int(month_str))][tx_type] += float(total or 0.0)
    monthly_summary = [
        MonthlySummary(year=year, month=month, total_income=vals["income"], total_expense=vals["expense"])
        for (year, month), vals in sorted(monthly_map.items())
    ]

    total_income = float(income_sum or 0.0)
    total_expense = float(expense_sum or 0.0)
    return FinancialSummary(
        total_income=total_income,
        total_expense=total_expense,
        balance=total_income - total_expense,
        category_breakdown=category_breakdown,
        monthly_summary=monthly_summary,
    )

