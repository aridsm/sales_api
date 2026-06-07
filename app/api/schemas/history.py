import uuid
from datetime import datetime
from pydantic import BaseModel

class HistoryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action_type: int
    entity_type: int
    entity_id: uuid.UUID | None
    description: str
    details: dict
    created_at: datetime

class HistoryBulkDelete(BaseModel):
    ids: list[uuid.UUID]
