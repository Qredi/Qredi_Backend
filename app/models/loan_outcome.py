import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import LoanStatus

if TYPE_CHECKING:
    from app.models.user import User


class LoanOutcome(Base):
    __tablename__ = "loan_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )  # UMKM borrower
    lender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    loan_amount: Mapped[float] = mapped_column(Float, nullable=False)
    loan_term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    days_past_due: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[LoanStatus] = mapped_column(
        SAEnum(LoanStatus, name="loan_status"), nullable=False, default=LoanStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    borrower: Mapped["User"] = relationship(
        back_populates="loans_as_borrower", foreign_keys=[user_id]
    )
    lender: Mapped["User"] = relationship(
        back_populates="loans_as_lender", foreign_keys=[lender_id]
    )

    def __repr__(self) -> str:
        return f"<LoanOutcome id={self.id} amount={self.loan_amount} status={self.status}>"