"""Service that orchestrates all scrapers and stores results in the database."""

import asyncio
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from backend.models.opportunity import Category, Discipline, Opportunity
from backend.scrapers.base import RawOpportunity
from backend.scrapers.bdns_scraper import BDNSScraper
from backend.scrapers.boe_api_scraper import BOEAPIScraper
from backend.scrapers.boe_scraper import BOEScraper
from backend.scrapers.comunidades_scraper import ComunidadesScraper
from backend.scrapers.cultura_gob import CulturaGobScraper
from backend.scrapers.fundaciones_scraper import FundacionesScraper
from backend.scrapers.rss_scraper import RSSScraper
from backend.scrapers.wordpress_scraper import WordPressScraper
from backend.scrapers.nuevas_fuentes_scraper import NuevasFuentesScraper

logger = logging.getLogger(__name__)

ALL_SCRAPERS = [
    BDNSScraper,       # Highest priority: all public subsidies via structured portal
    BOEAPIScraper,     # Official BOE API (JSON)
    RSSScraper,
    CulturaGobScraper,
    BOEScraper,
    FundacionesScraper,
    ComunidadesScraper,
    WordPressScraper,  # WordPress-based art sites (Exibart, masdearte, PAC, etc.)
    NuevasFuentesScraper,  # Nuevas fuentes: Injuve, SGAE, Teatros del Canal, Creative Europe, etc.
]

CATEGORY_MAP = {v.value: v for v in Category}
DISCIPLINE_MAP = {v.value: v for v in Discipline}


def _map_category(raw: str) -> Category:
    return CATEGORY_MAP.get(raw, Category.OTRO)


def _map_discipline(raw: str) -> Discipline:
    return DISCIPLINE_MAP.get(raw, Discipline.MULTIDISCIPLINAR)


def _raw_to_db(raw: RawOpportunity) -> dict:
    """Convert a RawOpportunity to a dict for database insertion."""
    return {
        "title": raw.title[:500],
        "description": raw.description[:5000] if raw.description else "",
        "category": _map_category(raw.category),
        "discipline": _map_discipline(raw.discipline),
        "organization": raw.organization,
        "source_name": raw.source_name,
        "source_url": raw.source_url,
        "location": raw.location,
        "region": raw.region,
        "deadline": raw.deadline,
        "start_date": raw.start_date,
        "end_date": raw.end_date,
        "publication_date": raw.publication_date,
        "funding_amount": raw.funding_amount,
    }


async def run_all_scrapers() -> list[RawOpportunity]:
    """Run all scrapers concurrently and collect results."""
    tasks = []
    for scraper_cls in ALL_SCRAPERS:
        scraper = scraper_cls()
        tasks.append(scraper.run())

    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    combined = []
    for result in all_results:
        if isinstance(result, Exception):
            logger.error(f"Scraper failed: {result}")
        elif isinstance(result, list):
            combined.extend(result)

    return combined


def store_opportunities(db: Session, raw_opps: list[RawOpportunity]) -> dict:
    """Store scraped opportunities, updating existing ones by source_url."""
    stats = {"new": 0, "updated": 0, "skipped": 0}

    for raw in raw_opps:
        try:
            existing = (
                db.query(Opportunity)
                .filter(Opportunity.source_url == raw.source_url)
                .first()
            )

            data = _raw_to_db(raw)

            if existing:
                for key, value in data.items():
                    if key != "source_url" and value:
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                stats["updated"] += 1
            else:
                opp = Opportunity(**data)
                db.add(opp)
                stats["new"] += 1

        except Exception as e:
            logger.error(f"Error storing opportunity '{raw.title[:50]}': {e}")
            stats["skipped"] += 1

    db.commit()
    return stats


async def scrape_and_store(db: Session) -> dict:
    """Main entry point: run all scrapers and store results."""
    logger.info("Starting full scrape cycle...")
    raw_opps = await run_all_scrapers()
    logger.info(f"Scraped {len(raw_opps)} total opportunities")

    stats = store_opportunities(db, raw_opps)
    logger.info(f"Store results: {stats}")
    return stats
