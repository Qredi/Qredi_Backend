from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.qris_transaction import QrisTransaction
from app.repositories.base_repository import BaseRepository


class QrisTransactionRepository(BaseRepository[QrisTransaction]):
    model = QrisTransaction

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[QrisTransaction]:
        return (
            self.db.query(QrisTransaction)
            .filter(QrisTransaction.user_id == user_id)
            .order_by(QrisTransaction.transaction_time.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_user_and_date_range(
        self, user_id: UUID, start: datetime, end: datetime
    ) -> List[QrisTransaction]:
        return (
            self.db.query(QrisTransaction)
            .filter(
                QrisTransaction.user_id == user_id,
                QrisTransaction.transaction_time >= start,
                QrisTransaction.transaction_time <= end,
            )
            .order_by(QrisTransaction.transaction_time.asc())
            .all()
        )

    def get_flagged_fraud(self, skip: int = 0, limit: int = 100) -> List[QrisTransaction]:
        return (
            self.db.query(QrisTransaction)
            .filter(QrisTransaction.fraud_flag.is_(True))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_reference(self, qris_reference: str) -> QrisTransaction | None:
        return (
            self.db.query(QrisTransaction)
            .filter(QrisTransaction.qris_reference == qris_reference)
            .first()
        )