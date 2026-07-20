from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.lender_profile_schemas import (
    LenderProfileCreate,
    LenderProfileUpdate,
    LenderProfileOut,
)
from app.services.lender_profile_service import LenderProfileService

router = APIRouter(prefix="/lender-profiles", tags=["lender_profiles"])


@router.post("/me", response_model=LenderProfileOut, status_code=status.HTTP_201_CREATED)
def create_my_profile(
    payload: LenderProfileCreate,
    current_user: User = Depends(require_roles(UserRole.LENDER)),
    db: Session = Depends(get_db),
):
    fields = payload.model_dump(exclude={"organization_id"})
    return LenderProfileService(db).create_for_user(
        current_user.id, payload.organization_id, **fields
    )


@router.get("/me", response_model=LenderProfileOut)
def get_my_profile(
    current_user: User = Depends(require_roles(UserRole.LENDER)),
    db: Session = Depends(get_db),
):
    return LenderProfileService(db).get_by_user(current_user.id)


@router.patch("/me", response_model=LenderProfileOut)
def update_my_profile(
    payload: LenderProfileUpdate,
    current_user: User = Depends(require_roles(UserRole.LENDER)),
    db: Session = Depends(get_db),
):
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    return LenderProfileService(db).update_for_user(current_user.id, **fields)


@router.get(
    "/by-organization/{organization_id}",
    response_model=List[LenderProfileOut],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def list_by_organization(organization_id: UUID, db: Session = Depends(get_db)):
    return LenderProfileService(db).list_by_organization(organization_id)