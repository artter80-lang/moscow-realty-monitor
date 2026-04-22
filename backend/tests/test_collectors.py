import pytest
import respx
from httpx import Response

from app.collectors.rss_collector import RssCollector, _is_relevant
from app.utils.deduplication import compute_hash

RSS_FIXTURE = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>Тест</title>
    <item>
      <title>Ипотека подорожала на фоне роста ключевой ставки</title>
      <link>https://example.com/news/1</link>
      <description>ЦБ поднял ставку, ипотечные ставки выросли.</description>
      <pubDate>Tue, 22 Apr 2026 09:00:00 +0300</pubDate>
    </item>
    <item>
      <title>Погода в Москве завтра</title>
      <link>https://example.com/news/2</link>
      <description>Ожидается дождь.</description>
    </item>
  </channel>
</rss>"""


def test_is_relevant_positive():
    assert _is_relevant("Ипотека в Москве выросла", "")
    assert _is_relevant("Новостройки дешевеют", "цены квартир")


def test_is_relevant_negative():
    assert not _is_relevant("Погода завтра в Тамбове", "Облачно без осадков")


def test_compute_hash_deterministic():
    h1 = compute_hash("Заголовок", "https://example.com")
    h2 = compute_hash("Заголовок", "https://example.com")
    assert h1 == h2
    assert len(h1) == 64


def test_compute_hash_different():
    h1 = compute_hash("A", "https://example.com/1")
    h2 = compute_hash("B", "https://example.com/2")
    assert h1 != h2


@pytest.mark.asyncio
async def test_rss_collector_filters_irrelevant():
    with respx.mock:
        respx.get("https://test.rss/feed").mock(return_value=Response(200, text=RSS_FIXTURE))
        collector = RssCollector(sources=[("Тест", "https://test.rss/feed")])
        events = await collector.collect()

    # Только первая новость релевантна
    assert len(events) == 1
    assert "ипотека" in events[0].title.lower() or "ставк" in events[0].title.lower()
