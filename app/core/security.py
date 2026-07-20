"""
app.core.security
==================

Single source of truth for authentication in this project.

Any service or router that needs to hash a password, issue/verify a token,
or gate an endpoint by role imports from here. Nothing else in the codebase
should directly interact with JWT or password hashing libraries.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository


# --------------------------------------------------------------------------
# Password hashing
# --------------------------------------------------------------------------

# Uses the recommended secure password hashing algorithm.
# Currently this is Argon2id.
password_hash = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return password_hash.hash(plain_password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    return password_hash.verify(plain_password, hashed_password)


# --------------------------------------------------------------------------
# OAuth2
# --------------------------------------------------------------------------

# Points at the auth router's login route.
# Used to generate the "Authorize" prompt in OpenAPI docs.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


# --------------------------------------------------------------------------
# JWT issuance / decoding
# --------------------------------------------------------------------------

def create_access_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Build a signed JWT.

    Args:
        subject: User ID represented as a string.
        role: User role.
        expires_delta: Optional custom expiration duration.
        extra_claims: Optional additional JWT claims.
    """
    now = datetime.now(timezone.utc)

    expire = now + (
        expires_delta
        or timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expire,
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

    except PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# --------------------------------------------------------------------------
# FastAPI dependencies
# --------------------------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolve the bearer token into a User row.

    Raises:
        HTTPException: If the token is invalid or the user does not exist.
    """
    payload = decode_access_token(token)

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserRepository(db).get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Resolve the current user and ensure the account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return current_user


def require_roles(*allowed_roles: UserRole):
    """
    Dependency factory for role-based access control.

    Example:

        current_user: User = Depends(
            require_roles(
                UserRole.ADMIN,
                UserRole.LENDER,
            )
        )
    """

    def _dependency(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Requires one of roles: "
                    f"{[role.value for role in allowed_roles]}"
                ),
            )

        return current_user

    return _dependency