from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.enums.company import CompanyPermission, InvitationStatus


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    logo_url: Optional[str] = None
    document: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    zip_code: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    logo_url: Optional[str] = None
    document: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    zip_code: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    logo_url: Optional[str] = None
    document: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    zip_code: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class CompanyResponse(CompanyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class CompanyUserAdd(BaseModel):
    email: EmailStr
    permission: CompanyPermission = CompanyPermission.VIEW


class CompanyUserUpdate(BaseModel):
    permission: Optional[CompanyPermission] = None
    job_title: Optional[str] = None
    user_job_title: Optional[str] = None


class CompanyUserResponse(BaseModel):
    id: UUID
    company_id: UUID
    user_id: UUID
    user_name: str | None = None
    user_email: str | None = None
    user_avatar_url: str | None = None
    user_phone: str | None = None
    user_job_title: str | None = None
    user_document: str | None = None
    user_zip_code: str | None = None
    user_street: str | None = None
    user_number: str | None = None
    user_complement: str | None = None
    user_neighborhood: str | None = None
    user_city: str | None = None
    user_state: str | None = None
    permission: CompanyPermission
    created_at: datetime


class CompanyListItem(CompanyBase):
    id: UUID
    permission: CompanyPermission
    created_at: datetime
    updated_at: datetime


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
