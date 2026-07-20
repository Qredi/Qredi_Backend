from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import MatchStatus


class MatchCreate(BaseModel):
    umkm_id: UUID
    match_score: Optional[float] = None
    recommended_limit: Optional[float] = None
    recommended_interest: Optional[float] = None
    reason: Optional[str] = None


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    umkm_id: UUID
    lender_id: UUID
    match_score: Optional[float]
    status: MatchStatus
    recommended_limit: Optional[float]
    recommended_interest: Optional[float]
    reason: Optional[str]