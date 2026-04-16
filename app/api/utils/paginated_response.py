from typing import List, Generic
from pydantic import BaseModel
from annotated_types import T


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total_items: int
    page: int
    total_pages: int
