# app/api/v1/acs_scoring.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.acs_score_schemas import ACSScoreResponse
from app.services.acs_client import ACSServiceError, acs_score_call

router = APIRouter(prefix="/acs-scores", tags=["acs_scores"])


@router.post("/{user_id}/score", response_model=ACSScoreResponse)
async def trigger_acs_score(
    user_id: UUID,
    technical_scope: bool = False,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    try:
        return await acs_score_call(user_id, technical_scope=technical_scope)
    except ACSServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))