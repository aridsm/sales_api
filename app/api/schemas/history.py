import uuid
from datetime import datetime
from pydantic import BaseModel

class HistoryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    created_by: uuid.UUID | None = None
    created_by_name: str | None = None
    created_by_email: str | None = None
    action_type: int
    entity_type: int
    entity_id: uuid.UUID | None
    description: str
    details: dict
    created_at: datetime

class HistoryBulkDelete(BaseModel):
    ids: list[uuid.UUID]
