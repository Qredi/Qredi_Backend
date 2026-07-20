from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.umkm_profile import UMKMProfile
from app.repositories.base_repository import BaseRepository


class UMKMProfileRepository(BaseRepository[UMKMProfile]):
    model = UMKMProfile

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_user_id(self, user_id: UUID) -> Optional[UMKMProfile]:
        return (
            self.db.query(UMKMProfile)
            .filter(UMKMProfile.user_id == user_id)
            .first()
        )

    def get_by_city(self, city: str) -> List[UMKMProfile]:
        return (
            self.db.query(UMKMProfile)
            .filter(UMKMProfile.city == city)
            .all()
        )

    def get_by_province(self, province: str) -> List[UMKMProfile]:
        return (
            self.db.query(UMKMProfile)
            .filter(UMKMProfile.province == province)
            .all()
        )