from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class OtherExpenseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    value: float = Field(..., gt=0)
    date: datetime
    category_id: UUID


class OtherExpenseCreate(OtherExpenseBase):
    @field_validator("description", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


class OtherExpenseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    value: Optional[float] = Field(None, gt=0)
    date: Optional[datetime] = Field(None)
    category_id: Optional[UUID] = Field(None)

    @field_validator("description", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v


class OtherExpenseResponse(OtherExpenseBase):
    id: UUID
    user_id: UUID
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_by_email: Optional[str] = None
    created_at: datetime
    category_name: Optional[str] = None
    category_color: Optional[str] = None


class OtherExpenseBulkDelete(BaseModel):
    ids: list[UUID]
