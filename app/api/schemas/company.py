from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.enums.company import CompanyPermission, InvitationStatus


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class CompanyUserAdd(BaseModel):
    email: EmailStr
    permission: CompanyPermission = CompanyPermission.VIEW


class CompanyUserUpdate(BaseModel):
    permission: CompanyPermission


class CompanyUserResponse(BaseModel):
    id: UUID
    company_id: UUID
    user_id: UUID
    user_name: str | None = None
    user_email: str | None = None
    permission: CompanyPermission
    created_at: datetime


class CompanyListItem(BaseModel):
    id: UUID
    name: str
    permission: CompanyPermission
    created_at: datetime


class SwitchCompanyRequest(BaseModel):
    company_id: UUID


class CompanyInvitationResponse(BaseModel):
    id: UUID
    company_id: UUID
    company_name: str | None = None
    invited_by_name: str | None = None
    invited_by_email: str | None = None
    user_id: UUID
    user_name: str | None = None
    user_email: str | None = None
    permission: CompanyPermission
    status: InvitationStatus
    created_at: datetime
