import asyncio
import json
import logging

import httpx

from app.analyzer.prompts import SYSTEM_PROMPT, USER_TEMPLATE
from app.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-haiku-4-5"

_semaphore = asyncio.Semaphore(5)


class ClaudeClient:
    """Клиент Claude через OpenRouter API."""

    async def analyze_event(self, title: str, summary: str | None) -> dict | None:
        user_message = USER_TEMPLATE.format(
            title=title,
            summary=summary or "Описание отсутствует",
        )
        payload = {
            "model": MODEL,
            "max_tokens": 256,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        }
        headers = {
            "Authorization": f"Bearer {settings.anthropic_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/moscow-realty-monitor",
        }
        async with _semaphore:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(OPENROUTER_URL, json=payload, headers=headers)
                    response.raise_for_status()
                raw_text = response.json()["choices"][0]["message"]["content"].strip()
                # убираем markdown-обёртку если есть
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("```")[1]
                    if raw_text.startswith("json"):
                        raw_text = raw_text[4:]
                return json.loads(raw_text)
            except json.JSONDecodeError as exc:
                logger.error("Невалидный JSON от модели: %s", exc)
                return None
            except httpx.HTTPError as exc:
                logger.error("Ошибка OpenRouter API: %s", exc)
                return None
