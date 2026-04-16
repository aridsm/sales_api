from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin:
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    id: UUID
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "bearer"


class RefreshToken(BaseModel):
    refresh_token: str
