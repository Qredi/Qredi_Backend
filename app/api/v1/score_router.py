from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_active_user, require_roles
from app.models.enums import RiskLevel, UserRole
from app.models.user import User
from app.schemas.score_schemas import ScoreCreate, ScoreOut
from app.services.score_service import ScoreService

router = APIRouter(prefix="/scores", tags=["scores"])


@router.post(
    "/",
    response_model=ScoreOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
    summary="Record a new ACS scoring-engine run for a user",
)
def record_score(payload: ScoreCreate, db: Session = Depends(get_db)):
    fields = payload.model_dump(exclude={"user_id", "acs_score"})
    return ScoreService(db).record_score(user_id=payload.user_id, acs_score=payload.acs_score, **fields)


@router.get("/me/latest", response_model=ScoreOut)
def get_my_latest_score(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return ScoreService(db).get_latest(current_user.id)


@router.get("/me/history", response_model=List[ScoreOut])
def get_my_score_history(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return ScoreService(db).get_history(current_user.id, skip=skip, limit=limit)


@router.get(
    "/by-user/{user_id}/latest",
    response_model=ScoreOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.LENDER))],
)
def get_latest_score_for_user(user_id: UUID, db: Session = Depends(get_db)):
    return ScoreService(db).get_latest(user_id)


@router.get(
    "/by-risk-level/{risk_level}",
    response_model=List[ScoreOut],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.LENDER))],
)
def list_by_risk_level(risk_level: RiskLevel, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return ScoreService(db).list_by_risk_level(risk_level, skip=skip, limit=limit)