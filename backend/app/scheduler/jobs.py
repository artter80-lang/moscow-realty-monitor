import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _collection_job():
    """Синхронная обёртка для запуска async collect из APScheduler."""
    from app.collectors.coordinator import run_collection

    asyncio.get_event_loop().create_task(run_collection())


def setup_scheduler() -> AsyncIOScheduler:
    scheduler.add_job(
        _collection_job,
        trigger=IntervalTrigger(hours=settings.collect_interval_hours),
        id="collect_job",
        replace_existing=True,
        misfire_grace_time=300,
    )
    logger.info(
        "Планировщик настроен: сбор каждые %d ч.", settings.collect_interval_hours
    )
    return scheduler
