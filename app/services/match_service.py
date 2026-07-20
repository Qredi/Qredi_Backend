from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import MatchStatus
from app.models.match import Match
from app.repositories.match_repository import MatchRepository


class MatchService:
    def __init__(self, db: Session):
        self.db = db
        self.match_repo = MatchRepository(db)

    def create(
        self,
        umkm_id: UUID,
        lender_id: UUID,
        match_score: Optional[float] = None,
        recommended_limit: Optional[float] = None,
        recommended_interest: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> Match:
        return self.match_repo.create(
            umkm_id=umkm_id,
            lender_id=lender_id,
            match_score=match_score,
            recommended_limit=recommended_limit,
            recommended_interest=recommended_interest,
            reason=reason,
            status=MatchStatus.PENDING,
        )

    def get(self, match_id: UUID) -> Match:
        match = self.match_repo.get(match_id)
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
        return match

    def list_for_umkm(self, umkm_id: UUID) -> List[Match]:
        return self.match_repo.get_by_umkm(umkm_id)

    def list_pending_for_lender(self, lender_id: UUID) -> List[Match]:
        return self.match_repo.get_pending_for_lender(lender_id)

    def accept(self, match_id: UUID) -> Match:
        return self._set_status(match_id, MatchStatus.ACCEPTED)

    def reject(self, match_id: UUID) -> Match:
        return self._set_status(match_id, MatchStatus.REJECTED)

    def expire(self, match_id: UUID) -> Match:
        return self._set_status(match_id, MatchStatus.EXPIRED)

    def _set_status(self, match_id: UUID, status_: MatchStatus) -> Match:
        match = self.match_repo.set_status(match_id, status_)
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
        return match