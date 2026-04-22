from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RawEvent:
    title: str
    url: str
    summary: str | None = None
    published_at: datetime | None = None
    external_id: str | None = None


class BaseCollector(ABC):
    source_name: str = ""

    @abstractmethod
    async def collect(self) -> list[RawEvent]:
        """Собрать сырые события из источника."""
