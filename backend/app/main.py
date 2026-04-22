import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import cbr, dashboard, events, trigger
from app.scheduler.jobs import scheduler, setup_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_scheduler()
    scheduler.start()
    logger.info("Планировщик запущен")
    yield
    scheduler.shutdown()
    logger.info("Планировщик остановлен")


app = FastAPI(
    title="Мониторинг рынка недвижимости Москвы",
    description="Сервис отслеживания ключевых событий, влияющих на цены новостроек",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(cbr.router)
app.include_router(dashboard.router)
app.include_router(trigger.router)

if (FRONTEND_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))


@app.get("/")
async def index(request: Request):
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")


@app.get("/events/{event_id}/detail")
async def event_detail_page(request: Request, event_id: int):
    return templates.TemplateResponse(request=request, name="event_detail.html", context={"event_id": event_id})
