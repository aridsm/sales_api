from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime
import uuid
from app.enums.company import CompanyPermission, InvitationStatus


class CompanyInvitation(SQLModel, table=True):
    __tablename__ = "company_invitations"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    company_id: uuid.UUID = Field(foreign_key="companies.id", nullable=False, index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    invited_by: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    permission: CompanyPermission = Field(default=CompanyPermission.VIEW, nullable=False)
    status: InvitationStatus = Field(default=InvitationStatus.PENDING, nullable=False, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
