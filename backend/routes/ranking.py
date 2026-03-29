"""
Ranking routes: score and rank jobs against candidate profiles.
"""

from fastapi import APIRouter, Request

from database import get_db
from services.ranking import rank_jobs
from models.schemas import RankJobsRequest, RankJobsResponse, RankedJob, JobListing
from utils.logger import setup_logger
from utils.rate_limiter import limiter
from utils.exceptions import NotFoundError

log = setup_logger("routes.ranking")
router = APIRouter(prefix="/api", tags=["Ranking"])


@router.post("/rank-jobs", response_model=RankJobsResponse)
@limiter.limit("10/minute")
async def rank_jobs_endpoint(request: Request, body: RankJobsRequest):
    """
    Rank jobs against a candidate profile.
    Supports rule_based, llm_based, or hybrid scoring methods.
    """
    db = get_db()

    # Fetch profile
    profile_doc = await db.profiles.find_one({"_id": body.profile_id})
    if not profile_doc:
        raise NotFoundError(f"Profile not found: {body.profile_id}")

    profile = profile_doc["profile"]

    # Fetch jobs — either specific IDs or all recent
    if body.job_ids:
        jobs = []
        for jid in body.job_ids:
            job = await db.jobs.find_one({"_id": jid})
            if job:
                jobs.append(job)
    else:
        cursor = db.jobs.find({})
        jobs = await cursor.to_list(length=50)

    if not jobs:
        raise NotFoundError("No jobs found to rank. Search for jobs first.")

    # Run ranking
    ranked, skill_gap = await rank_jobs(
        profile=profile,
        jobs=jobs,
        method=body.method.value if hasattr(body.method, 'value') else body.method,
    )

    # Persist match results
    for r in ranked:
        try:
            await db.matches.insert_one({
                "profile_id": body.profile_id,
                "job_id": r["job"].get("id", ""),
                "match_score": r["match_score"],
                "method": body.method.value if hasattr(body.method, 'value') else body.method,
            })
        except Exception:
            pass

    log.info(f"Ranked {len(ranked)} jobs for profile {body.profile_id} using {body.method}")

    return RankJobsResponse(
        profile_id=body.profile_id,
        method=body.method.value if hasattr(body.method, 'value') else body.method,
        ranked_jobs=[
            RankedJob(
                job=JobListing(**r["job"]) if isinstance(r["job"], dict) else r["job"],
                match_score=r["match_score"],
                matched_skills=r.get("matched_skills", []),
                missing_skills=r.get("missing_skills", []),
                explanation=r.get("explanation", ""),
                improvement_tips=r.get("improvement_tips", []),
            )
            for r in ranked
        ],
        skill_gap_summary=skill_gap,
    )