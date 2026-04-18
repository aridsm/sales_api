from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OtherExpenseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    value: float = Field(..., gt=0)
    date: date
    category_id: UUID


class OtherExpenseCreate(OtherExpenseBase):
    pass


class OtherExpenseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    value: Optional[float] = Field(None, gt=0)
    date: Optional[date] = None
    category_id: Optional[UUID] = None


class OtherExpenseResponse(OtherExpenseBase):
    id: UUID
    user_id: UUID
    created_at: datetime
