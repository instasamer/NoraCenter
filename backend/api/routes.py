"""API routes for the NoraCenter platform."""

import asyncio
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.opportunity import Category, Discipline, Opportunity
from backend.services.scraper_service import scrape_and_store

router = APIRouter()


@router.get("/api/opportunities")
def list_opportunities(
    q: str = Query("", description="Search text"),
    category: str = Query("", description="Filter by category"),
    discipline: str = Query("", description="Filter by discipline"),
    region: str = Query("", description="Filter by region"),
    active_only: bool = Query(True, description="Only show non-expired"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List opportunities with search and filters."""
    query = db.query(Opportunity)

    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                Opportunity.title.ilike(search),
                Opportunity.description.ilike(search),
                Opportunity.organization.ilike(search),
            )
        )

    if category:
        try:
            query = query.filter(Opportunity.category == Category(category))
        except ValueError:
            pass

    if discipline:
        try:
            query = query.filter(Opportunity.discipline == Discipline(discipline))
        except ValueError:
            pass

    if region:
        query = query.filter(Opportunity.region.ilike(f"%{region}%"))

    if active_only:
        now = datetime.utcnow()
        recent_cutoff = now - timedelta(days=90)
        query = query.filter(
            or_(
                # Has deadline and it's in the future
                Opportunity.deadline >= now,
                # No deadline but was scraped/published recently (last 90 days)
                and_(
                    Opportunity.deadline.is_(None),
                    or_(
                        Opportunity.publication_date >= recent_cutoff,
                        Opportunity.scraped_at >= recent_cutoff,
                    ),
                ),
            )
        )

    total = query.count()
    opportunities = (
        query.order_by(Opportunity.deadline.asc().nullslast(), Opportunity.scraped_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "results": [
            {
                "id": o.id,
                "title": o.title,
                "description": o.description[:300] if o.description else "",
                "category": o.category.value if o.category else None,
                "discipline": o.discipline.value if o.discipline else None,
                "organization": o.organization,
                "source_url": o.source_url,
                "source_name": o.source_name,
                "location": o.location,
                "region": o.region,
                "deadline": o.deadline.isoformat() if o.deadline else None,
                "publication_date": o.publication_date.isoformat() if o.publication_date else None,
                "funding_amount": o.funding_amount,
            }
            for o in opportunities
        ],
    }


@router.get("/api/opportunities/{opportunity_id}")
def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    """Get a single opportunity by ID."""
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        return {"error": "Not found"}, 404
    return {
        "id": opp.id,
        "title": opp.title,
        "description": opp.description,
        "category": opp.category.value if opp.category else None,
        "discipline": opp.discipline.value if opp.discipline else None,
        "organization": opp.organization,
        "source_url": opp.source_url,
        "source_name": opp.source_name,
        "location": opp.location,
        "region": opp.region,
        "deadline": opp.deadline.isoformat() if opp.deadline else None,
        "start_date": opp.start_date.isoformat() if opp.start_date else None,
        "end_date": opp.end_date.isoformat() if opp.end_date else None,
        "publication_date": opp.publication_date.isoformat() if opp.publication_date else None,
        "funding_amount": opp.funding_amount,
        "scraped_at": opp.scraped_at.isoformat() if opp.scraped_at else None,
    }


@router.get("/api/filters")
def get_filters(db: Session = Depends(get_db)):
    """Get available filter values."""
    regions = (
        db.query(Opportunity.region)
        .filter(Opportunity.region.isnot(None), Opportunity.region != "")
        .distinct()
        .all()
    )
    return {
        "categories": [{"value": c.value, "label": c.value.replace("_", " ").title()} for c in Category],
        "disciplines": [{"value": d.value, "label": d.value.replace("_", " ").title()} for d in Discipline],
        "regions": sorted([r[0] for r in regions]),
    }


@router.post("/api/scrape")
async def trigger_scrape(db: Session = Depends(get_db)):
    """Manually trigger a scrape cycle (admin endpoint)."""
    stats = await scrape_and_store(db)
    return {"status": "ok", "stats": stats}


@router.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get platform statistics."""
    total = db.query(Opportunity).count()
    now = datetime.utcnow()
    recent_cutoff = now - timedelta(days=90)
    active = db.query(Opportunity).filter(
        or_(
            Opportunity.deadline >= now,
            and_(
                Opportunity.deadline.is_(None),
                or_(
                    Opportunity.publication_date >= recent_cutoff,
                    Opportunity.scraped_at >= recent_cutoff,
                ),
            ),
        )
    ).count()
    sources = db.query(Opportunity.source_name).distinct().count()
    return {
        "total_opportunities": total,
        "active_opportunities": active,
        "sources": sources,
    }
