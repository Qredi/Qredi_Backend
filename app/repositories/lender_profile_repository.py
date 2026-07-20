from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.lender_profile import LenderProfile
from app.repositories.base_repository import BaseRepository


class LenderProfileRepository(BaseRepository[LenderProfile]):
    model = LenderProfile

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_user_id(self, user_id: UUID) -> Optional[LenderProfile]:
        return (
            self.db.query(LenderProfile)
            .filter(LenderProfile.user_id == user_id)
            .first()
        )

    def get_by_organization(self, organization_id: UUID) -> List[LenderProfile]:
        return (
            self.db.query(LenderProfile)
            .filter(LenderProfile.organization_id == organization_id)
            .all()
        )