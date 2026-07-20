from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import OrgType
from app.models.organization import Organization
from app.repositories.organization_repository import OrganizationRepository


class OrganizationService:
    def __init__(self, db: Session):
        self.db = db
        self.org_repo = OrganizationRepository(db)

    def create(self, name: str, type_: OrgType, license_no: Optional[str] = None) -> Organization:
        if self.org_repo.get_by_name(name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name already exists",
            )
        return self.org_repo.create(name=name, type=type_, license_no=license_no)

    def get(self, org_id: UUID) -> Organization:
        org = self.org_repo.get(org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        return org

    def list(self, active_only: bool = False, skip: int = 0, limit: int = 100) -> List[Organization]:
        if active_only:
            return self.org_repo.get_active()
        return self.org_repo.get_all(skip=skip, limit=limit)

    def update(self, org_id: UUID, **fields) -> Organization:
        org = self.org_repo.update(org_id, **fields)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        return org

    def deactivate(self, org_id: UUID) -> Organization:
        return self.update(org_id, is_active=False)