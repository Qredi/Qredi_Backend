from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_active_user, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.umkm_profile_schemas import UMKMProfileIn, UMKMProfileOut
from app.services.umkm_profile_service import UMKMProfileService

router = APIRouter(prefix="/umkm-profiles", tags=["umkm_profiles"])


def _ensure_self_or_admin(target_user_id: UUID, current_user: User):
    if current_user.role != UserRole.ADMIN and current_user.id != target_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")


@router.post("/me", response_model=UMKMProfileOut, status_code=status.HTTP_201_CREATED)
def create_my_profile(
    payload: UMKMProfileIn,
    current_user: User = Depends(require_roles(UserRole.UMKM)),
    db: Session = Depends(get_db),
):
    return UMKMProfileService(db).create_for_user(current_user.id, **payload.model_dump())


@router.get("/me", response_model=UMKMProfileOut)
def get_my_profile(
    current_user: User = Depends(require_roles(UserRole.UMKM)),
    db: Session = Depends(get_db),
):
    return UMKMProfileService(db).get_by_user(current_user.id)


@router.patch("/me", response_model=UMKMProfileOut)
def update_my_profile(
    payload: UMKMProfileIn,
    current_user: User = Depends(require_roles(UserRole.UMKM)),
    db: Session = Depends(get_db),
):
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    return UMKMProfileService(db).update_for_user(current_user.id, **fields)


@router.get("/by-user/{user_id}", response_model=UMKMProfileOut)
def get_profile_by_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _ensure_self_or_admin(user_id, current_user)
    return UMKMProfileService(db).get_by_user(user_id)


@router.get(
    "/",
    response_model=List[UMKMProfileOut],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.LENDER))],
)
def list_profiles(
    city: Optional[str] = None,
    province: Optional[str] = None,
    db: Session = Depends(get_db),
):
    service = UMKMProfileService(db)
    if city:
        return service.list_by_city(city)
    if province:
        return service.list_by_province(province)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Provide at least one filter: city or province",
    )