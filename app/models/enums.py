"""
Python enums mirroring the DBML `Enum` blocks.
"""

import enum


class UserRole(str, enum.Enum):
    UMKM = "umkm"
    LENDER = "lender"
    ADMIN = "admin"


class OrgType(str, enum.Enum):
    BANK = "bank"
    FINTECH = "fintech"
    COOPERATIVE = "cooperative"
    MULTIFINANCE = "multifinance"


class TransactionType(str, enum.Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    TRANSFER = "transfer"
    TOP_UP = "top_up"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LoanStatus(str, enum.Enum):
    ACTIVE = "active"
    PAID = "paid"
    OVERDUE = "overdue"
    DEFAULTED = "defaulted"


class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"