from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: str | None
    url: str | None
    published_at: datetime | None
    category: str | None
    impact_score: int | None
    price_direction: str | None
    is_key_event: bool
    status: str
    reasoning: str | None = None

    @classmethod
    def from_orm_with_reasoning(cls, event) -> "EventOut":
        obj = cls.model_validate(event)
        if event.analysis_raw and isinstance(event.analysis_raw, dict):
            obj.reasoning = event.analysis_raw.get("reasoning")
        return obj


class EventListResponse(BaseModel):
    items: list[EventOut]
    total: int
    limit: int
    offset: int
