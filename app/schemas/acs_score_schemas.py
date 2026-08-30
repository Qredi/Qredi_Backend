from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BusinessExplanation(BaseModel):
    category: str
    impact: str
    summary: str


class TopDriver(BaseModel):
    feature: str
    shap_contribution: float
    direction: str
    raw_value: float


class TechnicalExplanation(BaseModel):
    probability_of_default: float
    probability_of_default_raw_uncalibrated: float
    top_drivers: list[TopDriver]


class ACSScoreResponse(BaseModel):
    user_id: UUID
    acs_score: float
    risk_level: str
    model_version: str
    is_cold_start: bool
    transaction_count: int
    scored_at: datetime
    business_explanation: list[BusinessExplanation]
    technical_explanation: TechnicalExplanation | None = None