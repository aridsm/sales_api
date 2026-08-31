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

    # def __repr__(self):
    #     return f"<User(id={self.id}, email={self.email}, name={self.name})>"
