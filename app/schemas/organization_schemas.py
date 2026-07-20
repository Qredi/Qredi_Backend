from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import OrgType


class OrganizationCreate(BaseModel):
    name: str
    type: OrgType
    license_no: Optional[str] = None


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: OrgType
    license_no: Optional[str]
    is_active: bool