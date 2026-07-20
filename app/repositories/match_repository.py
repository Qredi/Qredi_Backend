from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.enums import MatchStatus
from app.repositories.base_repository import BaseRepository


class MatchRepository(BaseRepository[Match]):
    model = Match

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_umkm(self, umkm_id: UUID) -> List[Match]:
        return (
            self.db.query(Match)
            .filter(Match.umkm_id == umkm_id)
            .order_by(Match.created_at.desc())
            .all()
        )

    def get_by_lender(self, lender_id: UUID) -> List[Match]:
        return (
            self.db.query(Match)
            .filter(Match.lender_id == lender_id)
            .order_by(Match.created_at.desc())
            .all()
        )

    def get_by_status(self, status: MatchStatus) -> List[Match]:
        return self.db.query(Match).filter(Match.status == status).all()

    def get_pending_for_lender(self, lender_id: UUID) -> List[Match]:
        return (
            self.db.query(Match)
            .filter(Match.lender_id == lender_id, Match.status == MatchStatus.PENDING)
            .order_by(Match.match_score.desc())
            .all()
        )

    def set_status(self, match_id: UUID, status: MatchStatus) -> Match | None:
        return self.update(match_id, status=status)