"""
Auth business logic: registration + login. This is the only service that
touches `app.core.security`'s password/token functions directly — other
services rely on the router-level `require_roles` / `get_current_active_user`
dependencies instead of re-implementing auth checks themselves.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(
        self,
        email: str,
        password: str,
        full_name: str,
        role: UserRole,
        phone_number: Optional[str] = None,
    ) -> User:
        if self.user_repo.get_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        return self.user_repo.create(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            phone_number=phone_number,
        )

    def authenticate(self, email: str, password: str) -> User:
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
            )
        self.user_repo.update(user.id, last_login=datetime.now(timezone.utc))
        return user

    def login(self, email: str, password: str) -> dict:
        user = self.authenticate(email, password)
        token = create_access_token(subject=str(user.id), role=user.role.value)
        return {"access_token": token, "token_type": "bearer"}