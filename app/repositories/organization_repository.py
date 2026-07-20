from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.enums import OrgType
from app.repositories.base_repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    model = Organization

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_name(self, name: str) -> Optional[Organization]:
        return (
            self.db.query(Organization)
            .filter(Organization.name == name)
            .first()
        )

    def get_by_type(self, type_: OrgType) -> List[Organization]:
        return (
            self.db.query(Organization)
            .filter(Organization.type == type_)
            .all()
        )

    def get_active(self) -> List[Organization]:
        return (
            self.db.query(Organization)
            .filter(Organization.is_active.is_(True))
            .all()
        )