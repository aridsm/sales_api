from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy import DateTime
import uuid


class History(SQLModel, table=True):
    __tablename__ = "history"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    company_id: uuid.UUID = Field(foreign_key="companies.id", nullable=False, index=True)

    action_type: int = Field(nullable=False)
    entity_type: int = Field(nullable=False)

    entity_id: uuid.UUID | None = Field(default=None)

    description: str = Field(nullable=False)

    details: dict = Field(default_factory=dict, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False, sa_type=DateTime(timezone=True))
