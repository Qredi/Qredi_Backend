from typing import Any, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import RiskLevel
from app.models.score import Score
from app.repositories.score_repository import ScoreRepository

# Simple default thresholds for deriving a risk bucket from a 0-1000 ACS
# score when the scoring engine doesn't already provide one. Tune per model.
_RISK_THRESHOLDS = {
    RiskLevel.LOW: 700,
    RiskLevel.MEDIUM: 500,
}


def _derive_risk_level(acs_score: float) -> RiskLevel:
    if acs_score >= _RISK_THRESHOLDS[RiskLevel.LOW]:
        return RiskLevel.LOW
    if acs_score >= _RISK_THRESHOLDS[RiskLevel.MEDIUM]:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH


class ScoreService:
    def __init__(self, db: Session):
        self.db = db
        self.score_repo = ScoreRepository(db)

    def record_score(
        self,
        user_id: UUID,
        acs_score: float,
        risk_level: Optional[RiskLevel] = None,
        confidence_score: Optional[float] = None,
        prediction_label: Optional[str] = None,
        shap_values: Optional[Any] = None,
        top_features: Optional[Any] = None,
        rag_context: Optional[Any] = None,
        model_version: Optional[str] = None,
    ) -> Score:
        """Persist a new scoring run's output for a user."""
        return self.score_repo.create(
            user_id=user_id,
            acs_score=acs_score,
            risk_level=risk_level or _derive_risk_level(acs_score),
            confidence_score=confidence_score,
            prediction_label=prediction_label,
            shap_values=shap_values,
            top_features=top_features,
            rag_context=rag_context,
            model_version=model_version,
        )

    def get_latest(self, user_id: UUID) -> Score:
        score = self.score_repo.get_latest_for_user(user_id)
        if not score:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No score found for this user")
        return score

    def get_history(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Score]:
        return self.score_repo.get_history_for_user(user_id, skip=skip, limit=limit)

    def list_by_risk_level(self, risk_level: RiskLevel, skip: int = 0, limit: int = 100) -> List[Score]:
        return self.score_repo.get_by_risk_level(risk_level, skip=skip, limit=limit)