from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_active_user, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user_schemas import UserOut
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_my_profile(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(require_roles(UserRole.ADMIN))])
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    return UserService(db).get(user_id)


@router.get("/", response_model=List[UserOut], dependencies=[Depends(require_roles(UserRole.ADMIN))])
def list_users(
    role: Optional[UserRole] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return UserService(db).list_by_role(role, skip=skip, limit=limit)


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def deactivate_user(user_id: UUID, db: Session = Depends(get_db)):
    return UserService(db).deactivate(user_id)