import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import TransactionType

if TYPE_CHECKING:
    from app.models.user import User


class QrisTransaction(Base):
    __tablename__ = "qris_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, name="transaction_type"), nullable=False
    )
    merchant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    merchant_category: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    customer_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    qris_reference: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )
    transaction_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_refund: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fraud_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="qris_transactions")

    def __repr__(self) -> str:
        return (
            f"<QrisTransaction id={self.id} amount={self.amount} "
            f"type={self.transaction_type}>"
        )