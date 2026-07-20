from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def get(self, user_id: UUID) -> User:
        user = self.user_repo.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def list_by_role(self, role: Optional[UserRole], skip: int = 0, limit: int = 100) -> List[User]:
        if role:
            return self.user_repo.get_by_role(role, skip=skip, limit=limit)
        return self.user_repo.get_all(skip=skip, limit=limit)

    def deactivate(self, user_id: UUID) -> User:
        user = self.user_repo.deactivate(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user