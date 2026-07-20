from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import LoanStatus


class LoanOutcomeCreate(BaseModel):
    user_id: UUID  # UMKM borrower
    loan_amount: float
    loan_term_months: int
    due_date: datetime


class LoanOutcomeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    lender_id: UUID
    loan_amount: float
    loan_term_months: int
    due_date: datetime
    paid_at: Optional[datetime]
    days_past_due: Optional[int]
    status: LoanStatus