from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_active_user, require_role
from ..db import get_db
from ..models.user import User
from ..schemas.summary import FinancialSummary
from ..schemas.transaction import TransactionCreate, TransactionFilterParams, TransactionRead, TransactionUpdate
from ..services.transaction_service import (
    compute_summary,
    create_transaction,
    delete_transaction,
    get_transaction_by_id,
    get_transactions,
    update_transaction,
)
from ..utils.responses import api_response


router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
def create_tx(
    tx_in: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["analyst", "admin"])),
):
    tx = create_transaction(db, current_user, tx_in)
    return api_response(True, "Transaction created", TransactionRead.model_validate(tx).model_dump())


@router.get("/")
def list_txs(
    type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # viewers can read their own; analysts/admin can also read (admin sees all)
    try:
        filters = TransactionFilterParams(
            type=type,
            category=category,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    txs = get_transactions(db, current_user, filters)
    return api_response(
        True,
        "Transactions fetched",
        [TransactionRead.model_validate(tx).model_dump() for tx in txs],
    )


@router.get("/summary")
def summary(
    type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["analyst", "admin"])),
):
    try:
        filters = TransactionFilterParams(
            type=type,
            category=category,
            date_from=date_from,
            date_to=date_to,
            # summary ignores pagination but schema requires these fields
            limit=10,
            offset=0,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    result: FinancialSummary = compute_summary(db, current_user, filters)
    return api_response(True, "Summary computed", result.model_dump())


@router.get("/{transaction_id}")
def get_tx(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    tx = get_transaction_by_id(db, current_user, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return api_response(True, "Transaction fetched", TransactionRead.model_validate(tx).model_dump())


@router.put("/{transaction_id}")
def update_tx(
    transaction_id: int,
    tx_in: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["analyst", "admin"])),
):
    tx = update_transaction(db, current_user, transaction_id, tx_in)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return api_response(True, "Transaction updated", TransactionRead.model_validate(tx).model_dump())


@router.delete("/{transaction_id}")
def delete_tx(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["analyst", "admin"])),
):
    ok = delete_transaction(db, current_user, transaction_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return api_response(True, "Transaction deleted", None)

