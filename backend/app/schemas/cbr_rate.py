from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CbrRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rate_date: date
    rate_value: Decimal


class DashboardSummary(BaseModel):
    current_rate: Decimal | None
    previous_rate: Decimal | None
    rate_trend: str  # up | down | stable
    events_last_7d: int
    key_events_last_7d: int
    impact_distribution: dict[str, int]
    latest_key_events: list
