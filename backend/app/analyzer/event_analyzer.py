import logging
from datetime import datetime, timezone

from pydantic import BaseModel, field_validator

from app.analyzer.claude_client import ClaudeClient

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"cbr_rate", "mortgage", "regulation", "demand", "supply", "macro", "other"}
VALID_DIRECTIONS = {"up", "down", "neutral"}


class AnalysisResult(BaseModel):
    category: str
    impact_score: int
    price_direction: str
    is_key_event: bool
    reasoning: str

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        return v if v in VALID_CATEGORIES else "other"

    @field_validator("impact_score")
    @classmethod
    def validate_impact(cls, v: int) -> int:
        return max(-2, min(2, v))

    @field_validator("price_direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        return v if v in VALID_DIRECTIONS else "neutral"


class EventAnalyzer:
    def __init__(self):
        self._client = ClaudeClient()

    async def analyze(self, title: str, summary: str | None) -> AnalysisResult | None:
        raw = await self._client.analyze_event(title, summary)
        if raw is None:
            return None
        try:
            return AnalysisResult(**raw)
        except Exception as exc:
            logger.error("Ошибка валидации ответа Claude: %s | raw=%s", exc, raw)
            return None

    async def analyze_batch(
        self, items: list[tuple[int, str, str | None]]
    ) -> dict[int, AnalysisResult | None]:
        """Анализирует пачку событий. items = [(event_id, title, summary), ...]"""
        import asyncio

        results: dict[int, AnalysisResult | None] = {}
        batch_size = 10

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            tasks = [self.analyze(title, summary) for _, title, summary in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=False)
            for (event_id, _, _), result in zip(batch, batch_results):
                results[event_id] = result
            if i + batch_size < len(items):
                await asyncio.sleep(1)  # пауза между батчами
        return results
