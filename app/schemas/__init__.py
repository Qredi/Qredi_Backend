"""
Pydantic I/O schemas — kept fully separate from routers (which wire HTTP to
services) and services (which hold business logic). Naming convention:
`<Domain>Create` / `<Domain>Update` / `<Domain>In` for request bodies,
`<Domain>Out` for response models.
"""

from app.schemas.auth_schemas import RegisterRequest, TokenOut
from app.schemas.user_schemas import UserOut
from app.schemas.organization_schemas import OrganizationCreate, OrganizationOut
from app.schemas.umkm_profile_schemas import UMKMProfileIn, UMKMProfileOut
from app.schemas.lender_profile_schemas import (
    LenderProfileCreate,
    LenderProfileUpdate,
    LenderProfileOut,
)
from app.schemas.qris_transaction_schemas import (
    QrisTransactionCreate,
    QrisTransactionOut,
)
from app.schemas.score_schemas import ScoreCreate, ScoreOut
from app.schemas.loan_outcome_schemas import LoanOutcomeCreate, LoanOutcomeOut
from app.schemas.match_schemas import MatchCreate, MatchOut
from app.schemas.audit_log_schemas import AuditLogOut

__all__ = [
    "RegisterRequest",
    "TokenOut",
    "UserOut",
    "OrganizationCreate",
    "OrganizationOut",
    "UMKMProfileIn",
    "UMKMProfileOut",
    "LenderProfileCreate",
    "LenderProfileUpdate",
    "LenderProfileOut",
    "QrisTransactionCreate",
    "QrisTransactionOut",
    "ScoreCreate",
    "ScoreOut",
    "LoanOutcomeCreate",
    "LoanOutcomeOut",
    "MatchCreate",
    "MatchOut",
    "AuditLogOut",
]