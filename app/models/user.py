import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.umkm_profile import UMKMProfile
    from app.models.lender_profile import LenderProfile
    from app.models.qris_transaction import QrisTransaction
    from app.models.score import Score
    from app.models.loan_outcome import LoanOutcome
    from app.models.match import Match
    from app.models.audit_log import AuditLog


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"), nullable=False
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # 1:1 profiles
    umkm_profile: Mapped[Optional["UMKMProfile"]] = relationship(
        back_populates="user", uselist=False
    )
    lender_profile: Mapped[Optional["LenderProfile"]] = relationship(
        back_populates="user", uselist=False
    )

    # 1:N — this user's own QRIS activity
    qris_transactions: Mapped[List["QrisTransaction"]] = relationship(
        back_populates="user"
    )

    # 1:N — this user's own ACS scores
    scores: Mapped[List["Score"]] = relationship(back_populates="user")

    # loan_outcomes.user_id (UMKM borrower side)
    loans_as_borrower: Mapped[List["LoanOutcome"]] = relationship(
        back_populates="borrower",
        foreign_keys="LoanOutcome.user_id",
    )

    # loan_outcomes.lender_id
    loans_as_lender: Mapped[List["LoanOutcome"]] = relationship(
        back_populates="lender",
        foreign_keys="LoanOutcome.lender_id",
    )

    # matches.umkm_id
    matches_as_umkm: Mapped[List["Match"]] = relationship(
        back_populates="umkm",
        foreign_keys="Match.umkm_id",
    )

    # matches.lender_id
    matches_as_lender: Mapped[List["Match"]] = relationship(
        back_populates="lender",
        foreign_keys="Match.lender_id",
    )

    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"