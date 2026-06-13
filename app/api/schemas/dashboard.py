from pydantic import BaseModel
from enum import Enum

class FrequencyEnum(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"

class ChartItem(BaseModel):
    name: str
    revenue: float
    expenses: float
