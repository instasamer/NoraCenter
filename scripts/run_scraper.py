#!/usr/bin/env python3
"""CLI script to manually run scrapers and populate the database."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.models.database import SessionLocal, init_db
from backend.services.scraper_service import scrape_and_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


async def main():
    init_db()
    db = SessionLocal()
    try:
        stats = await scrape_and_store(db)
        print(f"\nScrape complete!")
        print(f"  New: {stats['new']}")
        print(f"  Updated: {stats['updated']}")
        print(f"  Skipped: {stats['skipped']}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
