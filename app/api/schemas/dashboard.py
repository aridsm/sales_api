from pydantic import BaseModel
from enum import Enum
from uuid import UUID
from typing import Optional

class FrequencyEnum(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"

class ChartItem(BaseModel):
    name: str
    revenue: float
    expenses: float

class BudgetResponse(BaseModel):
    current_balance: float
    net_profit: float
    revenue: float
    expenses: float

class TopProductItem(BaseModel):
    product_id: UUID
    product_name: str
    category_name: str
    category_color: Optional[str] = None
    quantity_sold: int
    total_revenue: float

