import logging
from datetime import date, datetime
from decimal import Decimal

from lxml import etree

from app.collectors.base import BaseCollector, RawEvent
from app.utils.http_client import fetch

logger = logging.getLogger(__name__)

CBR_KEY_RATE_URL = "https://cbr.ru/hd_base/KeyRate/"
CBR_KEY_RATE_XML = "https://cbr.ru/scripts/XML_val.asp?d=0"


class CbrCollector(BaseCollector):
    """Собирает данные о ключевой ставке ЦБ РФ."""

    source_name = "ЦБ РФ — Ключевая ставка"

    async def collect(self) -> list[RawEvent]:
        rate_info = await self._fetch_key_rate()
        if rate_info is None:
            return []
        rate_value, rate_date = rate_info
        return [
            RawEvent(
                title=f"ЦБ РФ: ключевая ставка {rate_value}% с {rate_date}",
                url=CBR_KEY_RATE_URL,
                summary=f"Банк России установил ключевую ставку на уровне {rate_value}% годовых.",
                published_at=datetime.combine(rate_date, datetime.min.time()),
                external_id=f"cbr_rate_{rate_date}",
            )
        ]

    async def get_current_rate(self) -> tuple[Decimal, date] | None:
        return await self._fetch_key_rate()

    async def _fetch_key_rate(self) -> tuple[Decimal, date] | None:
        try:
            response = await fetch(
                "https://cbr.ru/hd_base/KeyRate/",
                headers={"Accept": "text/html"},
            )
            # Парсим страницу ЦБ напрямую через XML API
            xml_response = await fetch(
                "https://cbr.ru/scripts/XML_dynamic.asp?date_req1=01/01/2024&date_req2=31/12/2026&VAL_NM_RQ=R01235"
            )
            # Используем альтернативный эндпоинт для ключевой ставки
            rate_response = await fetch(
                "https://cbr.ru/hd_base/KeyRate/?UniDbQuery.Posted=True&UniDbQuery.From=01.01.2024&UniDbQuery.To=31.12.2026"
            )
            logger.debug("CBR page fetched, length=%d", len(rate_response.text))
        except Exception as exc:
            logger.error("CBR fetch failed: %s", exc)
            return None

        # Парсируем HTML страницы статистики ключевой ставки
        try:
            return self._parse_cbr_html(rate_response.text)
        except Exception as exc:
            logger.error("CBR parse failed: %s", exc)
            return None

    def _parse_cbr_html(self, html: str) -> tuple[Decimal, date] | None:
        """Извлекает последнее значение ключевой ставки из HTML страницы ЦБ."""
        from lxml import html as lxml_html

        tree = lxml_html.fromstring(html)
        # Таблица на странице cbr.ru/hd_base/KeyRate/
        rows = tree.xpath('//table[contains(@class,"data")]//tr[position()>1]')
        if not rows:
            # fallback: ищем любую таблицу с данными о ставке
            rows = tree.xpath('//table//tr[td]')

        for row in rows:
            cells = row.xpath('.//td/text()')
            cells = [c.strip() for c in cells if c.strip()]
            if len(cells) >= 2:
                try:
                    rate_date = self._parse_date(cells[0])
                    rate_value = Decimal(cells[1].replace(",", ".").replace("%", "").strip())
                    if rate_date and 1 <= rate_value <= 100:
                        return rate_value, rate_date
                except (ValueError, Exception):
                    continue
        return None

    @staticmethod
    def _parse_date(date_str: str) -> date | None:
        for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None
