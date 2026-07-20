"""
Repository package — one CRUD repository per table, each subclassing
`BaseRepository` for the generic create/get/get_all/update/delete/count
operations and adding table-specific query methods on top.
"""

from app.repositories.base_repository import BaseRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.repositories.umkm_profile_repository import UMKMProfileRepository
from app.repositories.lender_profile_repository import LenderProfileRepository
from app.repositories.qris_transaction_repository import QrisTransactionRepository
from app.repositories.score_repository import ScoreRepository
from app.repositories.loan_outcome_repository import LoanOutcomeRepository
from app.repositories.match_repository import MatchRepository
from app.repositories.audit_log_repository import AuditLogRepository

__all__ = [
    "BaseRepository",
    "OrganizationRepository",
    "UserRepository",
    "UMKMProfileRepository",
    "LenderProfileRepository",
    "QrisTransactionRepository",
    "ScoreRepository",
    "LoanOutcomeRepository",
    "MatchRepository",
    "AuditLogRepository",
]