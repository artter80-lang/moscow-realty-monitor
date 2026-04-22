import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

HEADERS = {
    "User-Agent": "MoscowRealtyMonitor/1.0 (+https://github.com/example/moscow-realty-monitor)",
    "Accept-Language": "ru-RU,ru;q=0.9",
}


def get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(headers=HEADERS, timeout=30.0, follow_redirects=True)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch(url: str, **kwargs) -> httpx.Response:
    async with get_client() as client:
        response = await client.get(url, **kwargs)
        response.raise_for_status()
        return response
