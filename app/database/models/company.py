from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime
import uuid


class Company(SQLModel, table=True):
    __tablename__ = "companies"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
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
