from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.cbr_rate import CbrRate
from app.schemas.cbr_rate import CbrRateOut

router = APIRouter(prefix="/api/cbr", tags=["cbr"])


@router.get("/current", response_model=CbrRateOut | None)
async def get_current_rate(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CbrRate).order_by(CbrRate.rate_date.desc()).limit(1)
    )
    return result.scalar_one_or_none()


@router.get("/history", response_model=list[CbrRateOut])
async def get_rate_history(
    days: int = Query(90, ge=7, le=4000),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date, timedelta

    from_date = date.today() - timedelta(days=days)
    result = await db.execute(
        select(CbrRate)
        .where(CbrRate.rate_date >= from_date)
        .order_by(CbrRate.rate_date.asc())
    )
    return result.scalars().all()
