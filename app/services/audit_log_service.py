from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


class AuditLogService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_repo = AuditLogRepository(db)

    def log(
        self,
        action: str,
        user_id: Optional[UUID] = None,
        payload: Optional[Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        return self.audit_repo.log(
            action=action,
            user_id=user_id,
            payload=payload,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def list_for_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        return self.audit_repo.get_by_user(user_id, skip=skip, limit=limit)

    def list_by_action(self, action: str, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        return self.audit_repo.get_by_action(action, skip=skip, limit=limit)