import asyncio

from fastapi import APIRouter, Header, HTTPException

from app.config import settings

router = APIRouter(prefix="/api/collect", tags=["collect"])


@router.post("/run")
async def trigger_collection(x_secret_key: str = Header(default="")):
    if x_secret_key != settings.secret_key:
        raise HTTPException(status_code=403, detail="Неверный ключ")

    from app.collectors.coordinator import run_collection

    asyncio.get_event_loop().create_task(run_collection())
    return {"status": "started"}
