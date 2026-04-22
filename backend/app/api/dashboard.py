from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.cbr_rate import CbrRate
from app.models.event import Event
from app.schemas.cbr_rate import DashboardSummary
from app.schemas.event import EventOut

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(db: AsyncSession = Depends(get_db)):
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    # Ключевая ставка
    rates = (
        await db.execute(
            select(CbrRate).order_by(CbrRate.rate_date.desc()).limit(2)
        )
    ).scalars().all()
    current_rate = rates[0].rate_value if rates else None
    previous_rate = rates[1].rate_value if len(rates) > 1 else None

    if current_rate and previous_rate:
        rate_trend = "up" if current_rate > previous_rate else ("down" if current_rate < previous_rate else "stable")
    else:
        rate_trend = "stable"

    # Статистика событий за 7 дней
    events_last_7d = (
        await db.execute(
            select(func.count())
            .select_from(Event)
            .where(Event.status == "analyzed", Event.published_at >= week_ago)
        )
    ).scalar_one()

    key_events_last_7d = (
        await db.execute(
            select(func.count())
            .select_from(Event)
            .where(
                Event.status == "analyzed",
                Event.is_key_event.is_(True),
                Event.published_at >= week_ago,
            )
        )
    ).scalar_one()

    # Распределение по направлению цен
    direction_rows = (
        await db.execute(
            select(Event.price_direction, func.count())
            .where(Event.status == "analyzed", Event.published_at >= week_ago)
            .group_by(Event.price_direction)
        )
    ).all()
    impact_distribution = {row[0] or "neutral": row[1] for row in direction_rows}

    # Последние ключевые события
    latest_key = (
        await db.execute(
            select(Event)
            .where(Event.status == "analyzed", Event.is_key_event.is_(True))
            .order_by(Event.published_at.desc().nulls_last())
            .limit(5)
        )
    ).scalars().all()

    return DashboardSummary(
        current_rate=current_rate,
        previous_rate=previous_rate,
        rate_trend=rate_trend,
        events_last_7d=events_last_7d,
        key_events_last_7d=key_events_last_7d,
        impact_distribution=impact_distribution,
        latest_key_events=[EventOut.from_orm_with_reasoning(e) for e in latest_key],
    )
