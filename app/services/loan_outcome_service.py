from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import LoanStatus
from app.models.loan_outcome import LoanOutcome
from app.repositories.loan_outcome_repository import LoanOutcomeRepository


class LoanOutcomeService:
    def __init__(self, db: Session):
        self.db = db
        self.loan_repo = LoanOutcomeRepository(db)

    def create(
        self,
        user_id: UUID,
        lender_id: UUID,
        loan_amount: float,
        loan_term_months: int,
        due_date: datetime,
    ) -> LoanOutcome:
        return self.loan_repo.create(
            user_id=user_id,
            lender_id=lender_id,
            loan_amount=loan_amount,
            loan_term_months=loan_term_months,
            due_date=due_date,
            status=LoanStatus.ACTIVE,
        )

    def get(self, loan_id: UUID) -> LoanOutcome:
        loan = self.loan_repo.get(loan_id)
        if not loan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
        return loan

    def list_for_borrower(self, user_id: UUID) -> List[LoanOutcome]:
        return self.loan_repo.get_by_borrower(user_id)

    def list_for_lender(self, lender_id: UUID) -> List[LoanOutcome]:
        return self.loan_repo.get_by_lender(lender_id)

    def list_overdue(self) -> List[LoanOutcome]:
        return self.loan_repo.get_overdue(as_of=datetime.now(timezone.utc))

    def mark_paid(self, loan_id: UUID) -> LoanOutcome:
        loan = self.loan_repo.mark_paid(loan_id, paid_at=datetime.now(timezone.utc))
        if not loan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
        return loan

    def mark_defaulted(self, loan_id: UUID) -> LoanOutcome:
        loan = self.loan_repo.update(loan_id, status=LoanStatus.DEFAULTED)
        if not loan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
        return loan