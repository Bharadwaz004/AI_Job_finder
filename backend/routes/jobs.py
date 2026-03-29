"""
Job search routes: search by skills/roles, retrieve cached results.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Request, Query

from database import get_db
from services.job_search import search_jobs
from models.schemas import JobSearchRequest, JobSearchResponse, JobListing
from utils.logger import setup_logger
from utils.rate_limiter import limiter

log = setup_logger("routes.jobs")
router = APIRouter(prefix="/api", tags=["Jobs"])


@router.post("/jobs", response_model=JobSearchResponse)
@limiter.limit("15/minute")
async def search_jobs_endpoint(request: Request, body: JobSearchRequest):
    """
    Search for jobs matching given skills and roles.
    Results are cached for 30 minutes to minimize external API calls.
    """
    jobs, query_used, was_cached = await search_jobs(
        skills=body.skills,
        roles=body.roles,
        location=body.location,
        limit=body.limit,
        country=body.country,
    )

    # Persist jobs to DB for later ranking
    db = get_db()
    stored_count = 0
    for job in jobs:
        job_doc = {"_id": job["id"], **job, "searched_at": datetime.utcnow().isoformat()}
        try:
            await db.jobs.insert_one(job_doc)
            stored_count += 1
        except Exception as e:
            log.debug(f"Job insert skipped (likely duplicate): {job['id']} - {e}")

    log.info(f"Job search: {len(jobs)} results | stored={stored_count} | query='{query_used}' | cached={was_cached}")

    return JobSearchResponse(
        query_used=query_used,
        total=len(jobs),
        jobs=[JobListing(**j) for j in jobs],
        cached=was_cached,
    )


@router.get("/jobs/search")
@limiter.limit("15/minute")
async def search_jobs_get(
    request: Request,
    skills: str = Query(..., description="Comma-separated skills"),
    roles: str = Query("", description="Comma-separated roles"),
    location: str = Query("", description="Location filter"),
    country: str = Query("", description="Adzuna country code: gb, us, in, de, etc."),
    limit: int = Query(20, ge=1, le=50),
):
    """GET endpoint for quick job searches."""
    skill_list = [s.strip() for s in skills.split(",") if s.strip()]
    role_list = [r.strip() for r in roles.split(",") if r.strip()] if roles else []

    jobs, query_used, was_cached = await search_jobs(
        skills=skill_list,
        roles=role_list,
        location=location,
        limit=limit,
        country=country,
    )

    return JobSearchResponse(
        query_used=query_used,
        total=len(jobs),
        jobs=[JobListing(**j) for j in jobs],
        cached=was_cached,
    )