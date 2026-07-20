from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UMKMProfileIn(BaseModel):
    """Shared input shape for both create and update (all fields optional
    so `PATCH /me` can send only what's changing)."""

    business_name: Optional[str] = None
    business_type: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    monthly_revenue: Optional[float] = None
    years_operating: Optional[int] = None
    employee_count: Optional[int] = None


class UMKMProfileOut(UMKMProfileIn):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID