from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON
import uuid


class History(SQLModel, table=True):
    __tablename__ = "history"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)

    action_type: int = Field(nullable=False)
    entity_type: int = Field(nullable=False)

    entity_id: uuid.UUID | None = Field(default=None)

    description: str = Field(nullable=False)

    details: dict = Field(default={}, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
