from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import RiskLevel


class ScoreCreate(BaseModel):
    user_id: UUID
    acs_score: float
    risk_level: Optional[RiskLevel] = None
    confidence_score: Optional[float] = None
    prediction_label: Optional[str] = None
    shap_values: Optional[Any] = None
    top_features: Optional[Any] = None
    rag_context: Optional[Any] = None
    model_version: Optional[str] = None


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    acs_score: float
    risk_level: RiskLevel
    confidence_score: Optional[float]
    prediction_label: Optional[str]
    model_version: Optional[str]