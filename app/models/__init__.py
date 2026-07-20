"""
ORM models package.

Import from here (`from app.models import User, Score, ...`) so every model
is registered on the shared declarative `Base` before `Base.metadata.create_all`
or Alembic autogeneration runs.
"""

from app.models.enums import (
    LoanStatus,
    MatchStatus,
    OrgType,
    RiskLevel,
    TransactionType,
    UserRole,
)
from app.models.organization import Organization
from app.models.user import User
from app.models.umkm_profile import UMKMProfile
from app.models.lender_profile import LenderProfile
from app.models.qris_transaction import QrisTransaction
from app.models.score import Score
from app.models.loan_outcome import LoanOutcome
from app.models.match import Match
from app.models.audit_log import AuditLog

__all__ = [
    "LoanStatus",
    "MatchStatus",
    "OrgType",
    "RiskLevel",
    "TransactionType",
    "UserRole",
    "Organization",
    "User",
    "UMKMProfile",
    "LenderProfile",
    "QrisTransaction",
    "Score",
    "LoanOutcome",
    "Match",
    "AuditLog",
]