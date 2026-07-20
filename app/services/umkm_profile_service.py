from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.umkm_profile import UMKMProfile
from app.repositories.umkm_profile_repository import UMKMProfileRepository


class UMKMProfileService:
    def __init__(self, db: Session):
        self.db = db
        self.profile_repo = UMKMProfileRepository(db)

    def create_for_user(self, user_id: UUID, **fields) -> UMKMProfile:
        if self.profile_repo.get_by_user_id(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="UMKM profile already exists for this user",
            )
        return self.profile_repo.create(user_id=user_id, **fields)

    def get_by_user(self, user_id: UUID) -> UMKMProfile:
        profile = self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UMKM profile not found")
        return profile

    def update_for_user(self, user_id: UUID, **fields) -> UMKMProfile:
        profile = self.get_by_user(user_id)
        return self.profile_repo.update(profile.id, **fields)

    def list_by_city(self, city: str) -> List[UMKMProfile]:
        return self.profile_repo.get_by_city(city)

    def list_by_province(self, province: str) -> List[UMKMProfile]:
        return self.profile_repo.get_by_province(province)