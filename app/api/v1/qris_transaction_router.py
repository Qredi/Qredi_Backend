from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_active_user, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.qris_transaction_schemas import (
    QrisTransactionCreate,
    QrisTransactionOut,
)
from app.services.qris_transaction_service import QrisTransactionService

router = APIRouter(prefix="/qris-transactions", tags=["qris_transactions"])


@router.post(
    "/",
    response_model=QrisTransactionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
    summary="Ingest a QRIS transaction (system/admin import endpoint)",
)
def ingest_transaction(payload: QrisTransactionCreate, db: Session = Depends(get_db)):
    fields = payload.model_dump(exclude={"user_id", "amount", "transaction_type", "transaction_time"})
    return QrisTransactionService(db).ingest(
        user_id=payload.user_id,
        amount=payload.amount,
        transaction_type=payload.transaction_type,
        transaction_time=payload.transaction_time,
        **fields,
    )


@router.get("/me", response_model=List[QrisTransactionOut])
def list_my_transactions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return QrisTransactionService(db).list_for_user(current_user.id, skip=skip, limit=limit)


@router.get(
    "/by-user/{user_id}",
    response_model=List[QrisTransactionOut],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.LENDER))],
)
def list_transactions_for_user(user_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return QrisTransactionService(db).list_for_user(user_id, skip=skip, limit=limit)


@router.get(
    "/fraud-flagged",
    response_model=List[QrisTransactionOut],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def list_fraud_flagged(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return QrisTransactionService(db).list_flagged_fraud(skip=skip, limit=limit)