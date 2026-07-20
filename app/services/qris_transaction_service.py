from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import TransactionType
from app.models.qris_transaction import QrisTransaction
from app.repositories.qris_transaction_repository import QrisTransactionRepository


class QrisTransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.tx_repo = QrisTransactionRepository(db)

    def ingest(
        self,
        user_id: UUID,
        amount: float,
        transaction_type: TransactionType,
        transaction_time: datetime,
        **fields,
    ) -> QrisTransaction:
        """Record a single QRIS transaction (e.g. from a webhook/batch import)."""
        qris_reference = fields.get("qris_reference")
        if qris_reference and self.tx_repo.get_by_reference(qris_reference):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction with this qris_reference already exists",
            )
        return self.tx_repo.create(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            transaction_time=transaction_time,
            **fields,
        )

    def get(self, tx_id: UUID) -> QrisTransaction:
        tx = self.tx_repo.get(tx_id)
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return tx

    def list_for_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[QrisTransaction]:
        return self.tx_repo.get_by_user(user_id, skip=skip, limit=limit)

    def list_for_user_in_range(
        self, user_id: UUID, start: datetime, end: datetime
    ) -> List[QrisTransaction]:
        return self.tx_repo.get_by_user_and_date_range(user_id, start, end)

    def list_flagged_fraud(self, skip: int = 0, limit: int = 100) -> List[QrisTransaction]:
        return self.tx_repo.get_flagged_fraud(skip=skip, limit=limit)