from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_active_user, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.loan_outcome_schemas import LoanOutcomeCreate, LoanOutcomeOut
from app.services.loan_outcome_service import LoanOutcomeService

router = APIRouter(prefix="/loans", tags=["loan_outcomes"])


@router.post(
    "/",
    response_model=LoanOutcomeOut,
    dependencies=[Depends(require_roles(UserRole.LENDER))],
)
def create_loan(
    payload: LoanOutcomeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """The authenticated lender extends the loan to the given UMKM borrower."""
    return LoanOutcomeService(db).create(
        user_id=payload.user_id,
        lender_id=current_user.id,
        loan_amount=payload.loan_amount,
        loan_term_months=payload.loan_term_months,
        due_date=payload.due_date,
    )


@router.get("/{loan_id}", response_model=LoanOutcomeOut)
def get_loan(loan_id: UUID, db: Session = Depends(get_db)):
    return LoanOutcomeService(db).get(loan_id)


@router.get("/by-borrower/me", response_model=List[LoanOutcomeOut])
def list_my_loans_as_borrower(
    current_user: User = Depends(require_roles(UserRole.UMKM)),
    db: Session = Depends(get_db),
):
    return LoanOutcomeService(db).list_for_borrower(current_user.id)


@router.get("/by-lender/me", response_model=List[LoanOutcomeOut])
def list_my_loans_as_lender(
    current_user: User = Depends(require_roles(UserRole.LENDER)),
    db: Session = Depends(get_db),
):
    return LoanOutcomeService(db).list_for_lender(current_user.id)


@router.get(
    "/overdue",
    response_model=List[LoanOutcomeOut],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def list_overdue_loans(db: Session = Depends(get_db)):
    return LoanOutcomeService(db).list_overdue()


@router.patch(
    "/{loan_id}/mark-paid",
    response_model=LoanOutcomeOut,
    dependencies=[Depends(require_roles(UserRole.LENDER, UserRole.ADMIN))],
)
def mark_loan_paid(loan_id: UUID, db: Session = Depends(get_db)):
    return LoanOutcomeService(db).mark_paid(loan_id)


@router.patch(
    "/{loan_id}/mark-defaulted",
    response_model=LoanOutcomeOut,
    dependencies=[Depends(require_roles(UserRole.LENDER, UserRole.ADMIN))],
)
def mark_loan_defaulted(loan_id: UUID, db: Session = Depends(get_db)):
    return LoanOutcomeService(db).mark_defaulted(loan_id)