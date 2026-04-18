from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy.dialects.postgresql import UUID
import uuid


class User(SQLModel, table=True):
    """User model"""

    __tablename__ = "users"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    email: str = Field(max_length=255, unique=True, nullable=False, index=True)
    password_hash: str = Field(max_length=255, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # def __repr__(self):
    #     return f"<User(id={self.id}, email={self.email}, name={self.name})>"
