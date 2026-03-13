"""Main FastAPI application for NoraCenter."""

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from backend.api.routes import router as api_router
from backend.models.database import SessionLocal, init_db
from backend.services.scraper_service import scrape_and_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scheduled_scrape():
    """Run scrapers on schedule."""
    db = SessionLocal()
    try:
        await scrape_and_store(db)
    except Exception as e:
        logger.error(f"Scheduled scrape failed: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized")

    # Schedule daily scrape at 6:00 AM
    scheduler.add_job(scheduled_scrape, "cron", hour=6, minute=0, id="daily_scrape")
    # Also run every 12 hours for fresher data
    scheduler.add_job(scheduled_scrape, "interval", hours=12, id="periodic_scrape")
    scheduler.start()
    logger.info("Scheduler started")

    yield

    scheduler.shutdown()


app = FastAPI(
    title="NoraCenter",
    description="Plataforma de oportunidades para artistas en España",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

templates = Jinja2Templates(directory="frontend/templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
