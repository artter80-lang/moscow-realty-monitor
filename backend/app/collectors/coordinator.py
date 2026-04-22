import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzer.event_analyzer import EventAnalyzer
from app.collectors.base import RawEvent
from app.collectors.cbr_collector import CbrCollector
from app.collectors.rss_collector import RssCollector
from app.database import AsyncSessionLocal
from app.models.cbr_rate import CbrRate
from app.models.event import Event
from app.models.source import CollectionRun, Source
from app.utils.deduplication import compute_hash

logger = logging.getLogger(__name__)


async def _get_source_id(session: AsyncSession, name: str) -> int | None:
    result = await session.execute(select(Source.id).where(Source.name == name))
    return result.scalar_one_or_none()


async def _hash_exists(session: AsyncSession, content_hash: str) -> bool:
    result = await session.execute(
        select(Event.id).where(Event.content_hash == content_hash).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _save_events(
    session: AsyncSession,
    events: list[RawEvent],
    source_id: int | None,
) -> list[int]:
    """Сохраняет новые события, возвращает id созданных."""
    saved_ids = []
    for raw in events:
        content_hash = compute_hash(raw.title, raw.url or "")
        if await _hash_exists(session, content_hash):
            continue
        event = Event(
            source_id=source_id,
            external_id=raw.external_id,
            content_hash=content_hash,
            title=raw.title,
            summary=raw.summary,
            url=raw.url,
            published_at=raw.published_at,
            status="pending",
        )
        session.add(event)
        await session.flush()
        saved_ids.append(event.id)
    await session.commit()
    return saved_ids


async def _save_cbr_rate(session: AsyncSession, cbr: CbrCollector) -> None:
    rate_info = await cbr.get_current_rate()
    if rate_info is None:
        return
    rate_value, rate_date = rate_info
    existing = await session.execute(
        select(CbrRate.id).where(CbrRate.rate_date == rate_date).limit(1)
    )
    if existing.scalar_one_or_none() is not None:
        return
    session.add(CbrRate(rate_date=rate_date, rate_value=rate_value))
    await session.commit()
    logger.info("Ключевая ставка %s%% на %s сохранена", rate_value, rate_date)


async def _analyze_pending(session: AsyncSession, analyzer: EventAnalyzer) -> int:
    result = await session.execute(
        select(Event).where(Event.status == "pending").order_by(Event.collected_at).limit(50)
    )
    events = result.scalars().all()
    if not events:
        return 0

    items = [(e.id, e.title, e.summary) for e in events]
    analysis_map = await analyzer.analyze_batch(items)

    now = datetime.now(timezone.utc)
    analyzed = 0
    for event in events:
        result = analysis_map.get(event.id)
        if result is None:
            event.status = "failed"
            continue
        event.category = result.category
        event.impact_score = result.impact_score
        event.price_direction = result.price_direction
        event.is_key_event = result.is_key_event
        event.analysis_raw = result.model_dump()
        event.analyzed_at = now
        event.status = "analyzed"
        analyzed += 1

    await session.commit()
    return analyzed


async def run_collection() -> dict:
    """Главная функция сбора: запускает все коллекторы и анализ."""
    logger.info("Запуск сбора данных")
    analyzer = EventAnalyzer()
    stats = {"collected": 0, "analyzed": 0, "errors": []}

    run = CollectionRun(started_at=datetime.now(timezone.utc))
    async with AsyncSessionLocal() as session:
        session.add(run)
        await session.flush()
        run_id = run.id
        await session.commit()

    try:
        # 1. ЦБ РФ
        async with AsyncSessionLocal() as session:
            cbr = CbrCollector()
            await _save_cbr_rate(session, cbr)
            cbr_events = await cbr.collect()
            source_id = await _get_source_id(session, cbr.source_name)
            saved = await _save_events(session, cbr_events, source_id)
            stats["collected"] += len(saved)

        # 2. RSS
        async with AsyncSessionLocal() as session:
            rss = RssCollector()
            rss_events = await rss.collect()
            source_id = await _get_source_id(session, "РБК Недвижимость")  # используем первый RSS
            saved = await _save_events(session, rss_events, source_id)
            stats["collected"] += len(saved)

        # 3. Анализ всех pending
        async with AsyncSessionLocal() as session:
            analyzed = await _analyze_pending(session, analyzer)
            stats["analyzed"] = analyzed

        # 4. Завершаем run
        async with AsyncSessionLocal() as session:
            run_obj = await session.get(CollectionRun, run_id)
            if run_obj:
                run_obj.finished_at = datetime.now(timezone.utc)
                run_obj.status = "success"
                run_obj.events_collected = stats["collected"]
                run_obj.events_analyzed = stats["analyzed"]
                await session.commit()

    except Exception as exc:
        logger.exception("Ошибка во время сбора данных")
        stats["errors"].append(str(exc))
        async with AsyncSessionLocal() as session:
            run_obj = await session.get(CollectionRun, run_id)
            if run_obj:
                run_obj.finished_at = datetime.now(timezone.utc)
                run_obj.status = "failed"
                run_obj.error_message = str(exc)
                await session.commit()

    logger.info("Сбор завершён: %s", stats)
    return stats
