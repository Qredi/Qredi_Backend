from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.base_repository import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog

    def __init__(self, db: Session):
        super().__init__(db)

    def log(
        self,
        action: str,
        user_id: Optional[UUID] = None,
        payload: Optional[Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Convenience helper for writing an audit entry in one call."""
        return self.create(
            action=action,
            user_id=user_id,
            payload=payload,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_action(self, action: str, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )