import logging
from datetime import datetime, timezone

import feedparser

from app.collectors.base import BaseCollector, RawEvent
from app.utils.http_client import fetch

logger = logging.getLogger(__name__)

RSS_SOURCES = [
    ("Лента.ру Недвижимость", "https://lenta.ru/rss/news/realty"),
    ("РИА Новости Недвижимость", "https://realty.ria.ru/export/rss2/index.xml"),
    ("РБК", "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"),
    ("ТАСС", "https://tass.ru/rss/v2.xml"),
]

KEYWORDS = [
    "ипотека", "недвижимость", "новостройк", "квартир", "застройщик",
    "дду", "эскроу", "льготная ипотека", "ключевая ставка", "росреестр",
    "семейная ипотека", "ценность", "цен", "москва",
]


def _is_relevant(title: str, summary: str) -> bool:
    text = (title + " " + (summary or "")).lower()
    return any(kw in text for kw in KEYWORDS)


def _parse_published(entry) -> datetime | None:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass
    return None


class RssCollector(BaseCollector):
    """Собирает новости с RSS-лент источников рынка недвижимости."""

    source_name = "RSS"

    def __init__(self, sources: list[tuple[str, str]] | None = None):
        self.sources = sources or RSS_SOURCES

    async def collect(self) -> list[RawEvent]:
        all_events: list[RawEvent] = []
        for name, url in self.sources:
            events = await self._collect_one(name, url)
            all_events.extend(events)
            logger.info("RSS %s: собрано %d событий", name, len(events))
        return all_events

    async def _collect_one(self, name: str, url: str) -> list[RawEvent]:
        try:
            response = await fetch(url)
            feed = feedparser.parse(response.text)
        except Exception as exc:
            logger.warning("RSS fetch failed [%s / %s]: %s", name, url, exc)
            return []

        events = []
        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "").strip()
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            # Очищаем HTML-теги из summary
            summary = _strip_tags(summary).strip()

            if not title or not link:
                continue
            if not _is_relevant(title, summary):
                continue

            events.append(
                RawEvent(
                    title=title,
                    url=link,
                    summary=summary[:1000] if summary else None,
                    published_at=_parse_published(entry),
                    external_id=link,
                )
            )
        return events


def _strip_tags(text: str) -> str:
    """Удаляет HTML-теги из строки."""
    import re
    return re.sub(r"<[^>]+>", " ", text)
