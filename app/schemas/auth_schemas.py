from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    phone_number: Optional[str] = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str