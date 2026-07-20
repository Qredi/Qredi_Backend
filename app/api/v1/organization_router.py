from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_roles
from app.models.enums import UserRole
from app.schemas.organization_schemas import OrganizationCreate, OrganizationOut
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post(
    "/",
    response_model=OrganizationOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)):
    return OrganizationService(db).create(
        name=payload.name, type_=payload.type, license_no=payload.license_no
    )


@router.get("/{org_id}", response_model=OrganizationOut)
def get_organization(org_id: UUID, db: Session = Depends(get_db)):
    return OrganizationService(db).get(org_id)


@router.get("/", response_model=List[OrganizationOut])
def list_organizations(
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return OrganizationService(db).list(active_only=active_only, skip=skip, limit=limit)


@router.patch(
    "/{org_id}/deactivate",
    response_model=OrganizationOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def deactivate_organization(org_id: UUID, db: Session = Depends(get_db)):
    return OrganizationService(db).deactivate(org_id)