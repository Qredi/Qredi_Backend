import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import MatchStatus

if TYPE_CHECKING:
    from app.models.user import User


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    umkm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    lender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[MatchStatus] = mapped_column(
        SAEnum(MatchStatus, name="match_status"),
        nullable=False,
        default=MatchStatus.PENDING,
    )
    recommended_limit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recommended_interest: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    umkm: Mapped["User"] = relationship(
        back_populates="matches_as_umkm", foreign_keys=[umkm_id]
    )
    lender: Mapped["User"] = relationship(
        back_populates="matches_as_lender", foreign_keys=[lender_id]
    )

    def __repr__(self) -> str:
        return f"<Match id={self.id} status={self.status} score={self.match_score}>"