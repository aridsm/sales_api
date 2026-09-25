from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime
import uuid


class Company(SQLModel, table=True):
    __tablename__ = "companies"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    logo_url: str | None = Field(default=None)
    document: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    website: str | None = Field(default=None, max_length=150)
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
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
