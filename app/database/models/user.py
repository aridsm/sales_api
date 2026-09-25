from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid


class User(SQLModel, table=True):
    """User model"""

    __tablename__ = "users"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    email: str = Field(max_length=255, unique=True, nullable=False, index=True)
    password_hash: str = Field(max_length=255, nullable=False)
    company_id: uuid.UUID | None = Field(
        sa_column=Column(
            ForeignKey("companies.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
            default=None,
        ),
    )
    avatar_url: str | None = Field(default=None)
    phone: str | None = Field(default=None, max_length=20)
    document: str | None = Field(default=None, max_length=20)
    zip_code: str | None = Field(default=None, max_length=10)
    street: str | None = Field(default=None, max_length=150)
    number: str | None = Field(default=None, max_length=20)
    complement: str | None = Field(default=None, max_length=50)
    neighborhood: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=2)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
