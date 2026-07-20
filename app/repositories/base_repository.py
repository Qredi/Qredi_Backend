"""
Generic CRUD repository. Model-specific repositories subclass this and add
query methods relevant to that table (e.g. `get_by_email`).
"""

from typing import Any, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    model: Type[ModelType]

    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs: Any) -> ModelType:
        obj = self.model(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get(self, id: UUID) -> Optional[ModelType]:
        return self.db.get(self.model, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return (
            self.db.query(self.model)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, id: UUID, **kwargs: Any) -> Optional[ModelType]:
        obj = self.get(id)
        if obj is None:
            return None
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: UUID) -> bool:
        obj = self.get(id)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True

    def count(self) -> int:
        return self.db.query(self.model).count()