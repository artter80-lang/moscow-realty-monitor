"""Заливает исторические данные ключевой ставки ЦБ РФ с 2018 года."""
import asyncio
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import AsyncSessionLocal, engine
from app.models.cbr_rate import CbrRate
from app.database import Base

# Ключевая ставка ЦБ РФ: (дата_начала, значение)
# Источник: официальные решения Совета директоров ЦБ РФ
CBR_HISTORY = [
    ("2018-01-01", "7.75"),
    ("2018-02-12", "7.50"),
    ("2018-03-26", "7.25"),
    ("2018-09-17", "7.50"),
    ("2018-12-17", "7.75"),
    ("2019-06-17", "7.50"),
    ("2019-07-29", "7.25"),
    ("2019-09-09", "7.00"),
    ("2019-10-28", "6.50"),
    ("2019-12-16", "6.25"),
    ("2020-02-10", "6.00"),
    ("2020-04-27", "5.50"),
    ("2020-06-22", "4.50"),
    ("2020-07-27", "4.25"),
    ("2021-03-22", "4.50"),
    ("2021-04-26", "5.00"),
    ("2021-06-14", "5.50"),
    ("2021-07-26", "6.50"),
    ("2021-09-13", "6.75"),
    ("2021-10-25", "7.50"),
    ("2021-12-20", "8.50"),
    ("2022-02-14", "9.50"),
    ("2022-02-28", "20.00"),  # экстренное решение — вторжение
    ("2022-04-11", "17.00"),
    ("2022-05-04", "14.00"),
    ("2022-05-27", "11.00"),
    ("2022-06-10", "9.50"),
    ("2022-07-25", "8.00"),
    ("2022-09-16", "7.50"),
    ("2023-07-24", "8.50"),
    ("2023-08-15", "12.00"),  # экстренное — курс рубля
    ("2023-09-18", "13.00"),
    ("2023-10-27", "15.00"),
    ("2023-12-18", "16.00"),
    ("2024-07-26", "18.00"),
    ("2024-09-13", "19.00"),
    ("2024-10-25", "21.00"),
    ("2025-02-14", "21.00"),
    ("2025-04-25", "21.00"),
    ("2025-06-06", "20.00"),
    ("2025-07-25", "18.00"),
    ("2025-09-12", "16.00"),
    ("2025-10-24", "15.00"),
    ("2026-04-22", "15.00"),
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        added = 0
        for date_str, rate_str in CBR_HISTORY:
            rate_date = date.fromisoformat(date_str)
            existing = await session.execute(
                select(CbrRate).where(CbrRate.rate_date == rate_date)
            )
            if existing.scalar_one_or_none():
                continue
            session.add(CbrRate(rate_date=rate_date, rate_value=Decimal(rate_str)))
            added += 1
        await session.commit()
        print(f"Добавлено {added} записей ставки ЦБ")


asyncio.run(seed())
