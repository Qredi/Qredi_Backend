from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.loan_outcome import LoanOutcome
from app.models.enums import LoanStatus
from app.repositories.base_repository import BaseRepository


class LoanOutcomeRepository(BaseRepository[LoanOutcome]):
    model = LoanOutcome

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_borrower(self, user_id: UUID) -> List[LoanOutcome]:
        return (
            self.db.query(LoanOutcome)
            .filter(LoanOutcome.user_id == user_id)
            .order_by(LoanOutcome.created_at.desc())
            .all()
        )

    def get_by_lender(self, lender_id: UUID) -> List[LoanOutcome]:
        return (
            self.db.query(LoanOutcome)
            .filter(LoanOutcome.lender_id == lender_id)
            .order_by(LoanOutcome.created_at.desc())
            .all()
        )

    def get_by_status(self, status: LoanStatus) -> List[LoanOutcome]:
        return (
            self.db.query(LoanOutcome)
            .filter(LoanOutcome.status == status)
            .all()
        )

    def get_overdue(self, as_of: datetime | None = None) -> List[LoanOutcome]:
        as_of = as_of or datetime.utcnow()
        return (
            self.db.query(LoanOutcome)
            .filter(
                LoanOutcome.status == LoanStatus.ACTIVE,
                LoanOutcome.due_date < as_of,
            )
            .all()
        )

    def mark_paid(self, loan_id: UUID, paid_at: datetime) -> LoanOutcome | None:
        return self.update(loan_id, status=LoanStatus.PAID, paid_at=paid_at)