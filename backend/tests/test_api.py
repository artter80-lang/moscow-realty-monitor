import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.utils.deduplication import compute_hash


async def _seed_event(db: AsyncSession, title: str = "Тест", status: str = "analyzed") -> Event:
    event = Event(
        content_hash=compute_hash(title, f"https://example.com/{title}"),
        title=title,
        url=f"https://example.com/{title}",
        status=status,
        category="mortgage",
        impact_score=1,
        price_direction="up",
        is_key_event=False,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@pytest.mark.asyncio
async def test_get_events_empty(client: AsyncClient):
    r = await client.get("/api/events")
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_events_returns_analyzed(client: AsyncClient, db_session: AsyncSession):
    await _seed_event(db_session, "Ипотека выросла")
    r = await client.get("/api/events")
    assert r.status_code == 200
    assert r.json()["total"] == 1


@pytest.mark.asyncio
async def test_get_event_not_found(client: AsyncClient):
    r = await client.get("/api/events/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_event_by_id(client: AsyncClient, db_session: AsyncSession):
    event = await _seed_event(db_session, "Ключевая ставка")
    r = await client.get(f"/api/events/{event.id}")
    assert r.status_code == 200
    assert r.json()["title"] == "Ключевая ставка"


@pytest.mark.asyncio
async def test_dashboard_summary(client: AsyncClient):
    r = await client.get("/api/dashboard/summary")
    assert r.status_code == 200
    data = r.json()
    assert "events_last_7d" in data
    assert "rate_trend" in data
