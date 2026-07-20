from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_roles
from app.models.enums import UserRole
from app.schemas.audit_log_schemas import AuditLogOut
from app.services.audit_log_service import AuditLogService

router = APIRouter(
    prefix="/audit-logs",
    tags=["audit_logs"],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)


@router.get("/by-user/{user_id}", response_model=List[AuditLogOut])
def list_logs_for_user(user_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return AuditLogService(db).list_for_user(user_id, skip=skip, limit=limit)


@router.get("/by-action/{action}", response_model=List[AuditLogOut])
def list_logs_by_action(action: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return AuditLogService(db).list_by_action(action, skip=skip, limit=limit)