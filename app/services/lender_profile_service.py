from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.lender_profile import LenderProfile
from app.repositories.lender_profile_repository import LenderProfileRepository
from app.repositories.organization_repository import OrganizationRepository


class LenderProfileService:
    def __init__(self, db: Session):
        self.db = db
        self.profile_repo = LenderProfileRepository(db)
        self.org_repo = OrganizationRepository(db)

    def create_for_user(self, user_id: UUID, organization_id: UUID, **fields) -> LenderProfile:
        if self.profile_repo.get_by_user_id(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lender profile already exists for this user",
            )
        if not self.org_repo.get(organization_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        return self.profile_repo.create(user_id=user_id, organization_id=organization_id, **fields)

    def get_by_user(self, user_id: UUID) -> LenderProfile:
        profile = self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lender profile not found")
        return profile

    def update_for_user(self, user_id: UUID, **fields) -> LenderProfile:
        profile = self.get_by_user(user_id)
        return self.profile_repo.update(profile.id, **fields)

    def list_by_organization(self, organization_id: UUID) -> List[LenderProfile]:
        return self.profile_repo.get_by_organization(organization_id)