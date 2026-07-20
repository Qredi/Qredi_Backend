from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.score import Score
from app.models.enums import RiskLevel
from app.repositories.base_repository import BaseRepository


class ScoreRepository(BaseRepository[Score]):
    model = Score

    def __init__(self, db: Session):
        super().__init__(db)

    def get_latest_for_user(self, user_id: UUID) -> Optional[Score]:
        return (
            self.db.query(Score)
            .filter(Score.user_id == user_id)
            .order_by(Score.created_at.desc())
            .first()
        )

    def get_history_for_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Score]:
        return (
            self.db.query(Score)
            .filter(Score.user_id == user_id)
            .order_by(Score.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_risk_level(
        self, risk_level: RiskLevel, skip: int = 0, limit: int = 100
    ) -> List[Score]:
        return (
            self.db.query(Score)
            .filter(Score.risk_level == risk_level)
            .offset(skip)
            .limit(limit)
            .all()
        )