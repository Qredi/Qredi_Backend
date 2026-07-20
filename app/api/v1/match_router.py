from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.match_schemas import MatchCreate, MatchOut
from app.services.match_service import MatchService

router = APIRouter(prefix="/matches", tags=["matches"])

# NOTE: literal-path routes (/by-umkm/me, /by-lender/me/pending) must be
# declared before the dynamic "/{match_id}" route below, otherwise FastAPI
# matches them against "/{match_id}" first and fails UUID parsing (422).


@router.post(
    "/",
    response_model=MatchOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.LENDER, UserRole.ADMIN))],
    summary="Propose a match between a UMKM and the authenticated lender",
)
def create_match(
    payload: MatchCreate,
    current_user: User = Depends(require_roles(UserRole.LENDER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    fields = payload.model_dump(exclude={"umkm_id"})
    return MatchService(db).create(umkm_id=payload.umkm_id, lender_id=current_user.id, **fields)


@router.get("/by-umkm/me", response_model=List[MatchOut])
def list_my_matches_as_umkm(
    current_user: User = Depends(require_roles(UserRole.UMKM)),
    db: Session = Depends(get_db),
):
    return MatchService(db).list_for_umkm(current_user.id)


@router.get("/by-lender/me/pending", response_model=List[MatchOut])
def list_my_pending_matches_as_lender(
    current_user: User = Depends(require_roles(UserRole.LENDER)),
    db: Session = Depends(get_db),
):
    return MatchService(db).list_pending_for_lender(current_user.id)


@router.get("/{match_id}", response_model=MatchOut)
def get_match(match_id: UUID, db: Session = Depends(get_db)):
    return MatchService(db).get(match_id)


@router.patch(
    "/{match_id}/accept",
    response_model=MatchOut,
    dependencies=[Depends(require_roles(UserRole.LENDER, UserRole.UMKM))],
)
def accept_match(match_id: UUID, db: Session = Depends(get_db)):
    return MatchService(db).accept(match_id)


@router.patch(
    "/{match_id}/reject",
    response_model=MatchOut,
    dependencies=[Depends(require_roles(UserRole.LENDER, UserRole.UMKM))],
)
def reject_match(match_id: UUID, db: Session = Depends(get_db)):
    return MatchService(db).reject(match_id)


@router.patch(
    "/{match_id}/expire",
    response_model=MatchOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def expire_match(match_id: UUID, db: Session = Depends(get_db)):
    return MatchService(db).expire(match_id)