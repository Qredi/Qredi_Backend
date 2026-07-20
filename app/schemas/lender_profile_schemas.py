from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LenderProfileCreate(BaseModel):
    organization_id: UUID
    position: Optional[str] = None
    max_loan_amount: Optional[float] = None
    min_acs_score: Optional[float] = None


class LenderProfileUpdate(BaseModel):
    position: Optional[str] = None
    max_loan_amount: Optional[float] = None
    min_acs_score: Optional[float] = None


class LenderProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    organization_id: UUID
    position: Optional[str]
    max_loan_amount: Optional[float]
    min_acs_score: Optional[float]