from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event
from app.schemas.event import EventListResponse, EventOut

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=EventListResponse)
async def list_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    category: str | None = None,
    price_direction: str | None = None,
    key_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    query = select(Event).where(Event.status == "analyzed")
    count_query = select(func.count()).select_from(Event).where(Event.status == "analyzed")

    if category:
        query = query.where(Event.category == category)
        count_query = count_query.where(Event.category == category)
    if price_direction:
        query = query.where(Event.price_direction == price_direction)
        count_query = count_query.where(Event.price_direction == price_direction)
    if key_only:
        query = query.where(Event.is_key_event.is_(True))
        count_query = count_query.where(Event.is_key_event.is_(True))

    total = (await db.execute(count_query)).scalar_one()
    events = (
        await db.execute(
            query.order_by(Event.published_at.desc().nulls_last()).limit(limit).offset(offset)
        )
    ).scalars().all()

    return EventListResponse(
        items=[EventOut.from_orm_with_reasoning(e) for e in events],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{event_id}", response_model=EventOut)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    event = await db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return EventOut.from_orm_with_reasoning(event)
