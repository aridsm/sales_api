from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime, Column, ForeignKey
import uuid
from app.enums.company import CompanyPermission, InvitationStatus


class CompanyInvitation(SQLModel, table=True):
    __tablename__ = "company_invitations"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    company_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
        ),
    )
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    invited_by: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    permission: CompanyPermission = Field(
        default=CompanyPermission.VIEW, nullable=False
    )
    status: InvitationStatus = Field(
        default=InvitationStatus.PENDING, nullable=False, index=True
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
