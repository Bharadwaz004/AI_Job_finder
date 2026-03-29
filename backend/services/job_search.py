"""
Job search service using the Adzuna API.
- Primary: Adzuna REST API (free tier, 12 countries including India)
- Fallback: Mock data for development/demo

Register for free API keys at: https://developer.adzuna.com/

Supported country codes:
  gb (UK), us (USA), de (Germany), fr (France), au (Australia),
  in (India), ca (Canada), nz (New Zealand), pl (Poland),
  br (Brazil), at (Austria), za (South Africa)

Results are cached to minimize API calls.
"""

import hashlib
import re
import uuid
from datetime import datetime, timezone

import httpx

from config import get_settings
from utils.logger import setup_logger
from utils.cache import get_cache, make_cache_key
from utils.exceptions import JobSearchError
from models.schemas import JobListing

log = setup_logger("job_search")

JOB_CACHE_TTL = 1800  # 30 minutes

# Adzuna API base
ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"


# ══════════════════════════════════════════════
#  Adzuna Integration
# ══════════════════════════════════════════════

async def search_adzuna(
    query: str,
    location: str = "",
    limit: int = 20,
    country: str = "",
) -> list[dict]:
    """
    Search jobs via the Adzuna REST API.

    Endpoint: GET /v1/api/jobs/{country}/search/{page}
    Docs: https://developer.adzuna.com/docs/search
    """
    settings = get_settings()

    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        log.warning("No Adzuna credentials configured — falling back to mock data")
        return await _mock_job_search(query, location, limit)

    country_code = country or settings.adzuna_country or "in"

    # Adzuna caps at 50 results per page
    results_per_page = min(limit, 50)

    params = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "what": query,
        "results_per_page": results_per_page,
        "content-type": "application/json",
        "sort_by": "relevance",
    }

    if location:
        params["where"] = location

    url = f"{ADZUNA_BASE}/{country_code}/search/1"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)

            if response.status_code == 401:
                log.error("Adzuna 401: Invalid app_id or app_key")
                raise JobSearchError(
                    "Adzuna authentication failed. Check ADZUNA_APP_ID and ADZUNA_APP_KEY in .env"
                )

            if response.status_code == 400:
                log.error(f"Adzuna 400: Bad request — {response.text[:300]}")
                raise JobSearchError(f"Adzuna rejected the query: {response.text[:200]}")

            if response.status_code != 200:
                log.error(f"Adzuna error {response.status_code}: {response.text[:300]}")
                raise JobSearchError(f"Adzuna API returned status {response.status_code}")

            data = response.json()
            raw_jobs = data.get("results", [])

            jobs = []
            for j in raw_jobs[:limit]:
                # Build a stable ID from title + company
                title = j.get("title", "")
                company = (j.get("company", {}) or {}).get("display_name", "")
                job_id = hashlib.md5(
                    f"{title}{company}{j.get('id', '')}".encode()
                ).hexdigest()[:12]

                # Location from Adzuna's nested structure
                loc_obj = j.get("location", {}) or {}
                loc_display = loc_obj.get("display_name", "")

                # Salary — combine min/max if available
                salary_parts = []
                if j.get("salary_min"):
                    salary_parts.append(f"₹{int(j['salary_min']):,}")
                if j.get("salary_max"):
                    salary_parts.append(f"₹{int(j['salary_max']):,}")
                salary = " – ".join(salary_parts) if salary_parts else ""

                jobs.append({
                    "id": job_id,
                    "title": _clean_html(title),
                    "company": company,
                    "location": loc_display,
                    "description": _clean_html(j.get("description", ""))[:1000],
                    "link": j.get("redirect_url", ""),
                    "source": "adzuna",
                    "posted_date": _format_date(j.get("created", "")),
                    "salary": salary,
                })

            log.info(
                f"Adzuna returned {len(jobs)} jobs for query='{query}' "
                f"country={country_code} location='{location}'"
            )
            return jobs

    except JobSearchError:
        raise
    except httpx.TimeoutException:
        log.error("Adzuna request timed out")
        raise JobSearchError("Job search timed out. Please try again.")
    except Exception as e:
        log.error(f"Adzuna request failed: {e}")
        raise JobSearchError(f"Job search failed: {str(e)}")


def _clean_html(text: str) -> str:
    """Strip basic HTML tags from Adzuna descriptions."""
    return re.sub(r"<[^>]+>", "", text).strip()


def _format_date(iso_date: str) -> str:
    """Convert ISO date to a human-readable relative string."""
    if not iso_date:
        return ""
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days = (now - dt).days
        if days == 0:
            return "Today"
        elif days == 1:
            return "Yesterday"
        elif days < 7:
            return f"{days} days ago"
        elif days < 30:
            return f"{days // 7} weeks ago"
        else:
            return f"{days // 30} months ago"
    except Exception:
        return iso_date[:10] if len(iso_date) >= 10 else iso_date


# ══════════════════════════════════════════════
#  Mock Data (Development / Demo)
# ══════════════════════════════════════════════

async def _mock_job_search(query: str, location: str, limit: int) -> list[dict]:
    """Generate realistic mock job data for development without API keys."""
    log.info(f"Using mock job data for query: {query}")

    templates = [
        {
            "title": "Senior Software Engineer",
            "company": "TechCorp Inc.",
            "location": "Bangalore, India",
            "description": f"Looking for a Senior Software Engineer with expertise in {query}. "
                         "Build scalable microservices, mentor junior engineers, drive technical decisions. "
                         "Requirements: 3+ years, Python, REST APIs, cloud (AWS/GCP), Docker, CI/CD.",
            "salary": "₹18,00,000 – ₹30,00,000",
        },
        {
            "title": "Full Stack Developer",
            "company": "InnovateTech Solutions",
            "location": "Hyderabad, India",
            "description": f"Join our product team as a Full Stack Developer. React, Node.js, and {query}. "
                         "Build user-facing features, optimize performance, collaborate with designers. "
                         "Requirements: React, TypeScript, PostgreSQL, Git, Agile.",
            "salary": "₹12,00,000 – ₹22,00,000",
        },
        {
            "title": "Data Engineer",
            "company": "DataDriven Analytics",
            "location": "Remote, India",
            "description": f"Design and maintain data pipelines using {query} and modern data stack. "
                         "BigQuery, Airflow, dbt, and Python. ETL optimization and data quality monitoring. "
                         "Requirements: SQL, Python, Spark, cloud data warehouses, 2+ years.",
            "salary": "₹15,00,000 – ₹28,00,000",
        },
        {
            "title": "AI/ML Engineer",
            "company": "NeuralWorks AI",
            "location": "Pune, India",
            "description": f"Build and deploy ML models in production. {query}, "
                         "deep learning (PyTorch/TensorFlow), MLOps, LLM fine-tuning. "
                         "Requirements: Python, ML algorithms, model deployment, FastAPI, Docker.",
            "salary": "₹20,00,000 – ₹35,00,000",
        },
        {
            "title": "Backend Developer",
            "company": "ScaleUp Systems",
            "location": "Chennai, India",
            "description": f"Build high-performance backend services using {query}. "
                         "Design APIs, optimize databases, implement caching. "
                         "Requirements: Python/Go, PostgreSQL, Redis, Kubernetes, system design.",
            "salary": "₹14,00,000 – ₹25,00,000",
        },
        {
            "title": "DevOps Engineer",
            "company": "CloudFirst Technologies",
            "location": "Bangalore, India",
            "description": f"Manage cloud infrastructure and CI/CD pipelines. {query}, "
                         "Terraform, Kubernetes, monitoring (Prometheus, Grafana). "
                         "Requirements: AWS/GCP, Docker, Linux, scripting, 2+ years.",
            "salary": "₹16,00,000 – ₹30,00,000",
        },
        {
            "title": "Product Analyst",
            "company": "GrowthMetrics",
            "location": "Mumbai, India",
            "description": f"Drive product decisions with data. Analyze user behavior using {query}, "
                         "build dashboards, run A/B experiments, present insights to stakeholders. "
                         "Requirements: SQL, Python, Tableau/Looker, statistical analysis.",
            "salary": "₹10,00,000 – ₹20,00,000",
        },
        {
            "title": "Frontend Engineer",
            "company": "PixelPerfect Labs",
            "location": "Remote",
            "description": f"Craft delightful UIs using React, TypeScript, and {query}. "
                         "Performance optimization, accessibility, design systems, component libraries. "
                         "Requirements: React, CSS/Tailwind, testing, 2+ years.",
            "salary": "₹12,00,000 – ₹24,00,000",
        },
    ]

    jobs = []
    for i, tmpl in enumerate(templates[:limit]):
        jobs.append({
            "id": uuid.uuid4().hex[:12],
            "title": tmpl["title"],
            "company": tmpl["company"],
            "location": location or tmpl["location"],
            "description": tmpl["description"],
            "link": f"https://www.adzuna.co.in/jobs/details/{uuid.uuid4().hex[:8]}",
            "source": "mock",
            "posted_date": f"{i + 1} days ago",
            "salary": tmpl["salary"],
        })

    return jobs


# ══════════════════════════════════════════════
#  Public API (with caching)
# ══════════════════════════════════════════════

async def search_jobs(
    skills: list[str],
    roles: list[str] = None,
    location: str = "",
    limit: int = 20,
    country: str = "",
) -> tuple[list[dict], str, bool]:
    """
    Search for jobs matching skills and roles.
    
    Strategy: Adzuna works best with short queries (2-4 words).
    We run multiple focused searches and merge/deduplicate results:
      1. Each suggested role as its own query (e.g. "Software Engineer")
      2. A skills-based fallback query (top 2-3 clean skill keywords)
    
    Returns (jobs, query_summary, was_cached).
    """
    # ── Clean inputs ──
    clean_skills = _clean_skill_list(skills)
    clean_roles = [_clean_query_term(r) for r in (roles or []) if r.strip()]

    # ── Build focused queries ──
    queries = []

    # Primary: one query per role (most effective on Adzuna)
    for role in clean_roles[:3]:
        if role:
            queries.append(role)

    # Secondary: top skills as a short query (fallback if no roles)
    if clean_skills:
        skill_query = " ".join(clean_skills[:3])
        queries.append(skill_query)

    # If somehow empty, use raw first skill
    if not queries:
        queries.append(skills[0] if skills else "developer")

    # Deduplicate queries
    seen_queries = set()
    unique_queries = []
    for q in queries:
        q_lower = q.lower().strip()
        if q_lower and q_lower not in seen_queries:
            seen_queries.add(q_lower)
            unique_queries.append(q)

    # ── Check cache (keyed on the full set of queries) ──
    cache = await get_cache()
    query_summary = " | ".join(unique_queries)
    cache_key = make_cache_key("jobs", query_summary, location, country, str(limit))
    cached = await cache.get(cache_key)

    if cached:
        log.info(f"Returning {len(cached)} cached jobs for: {query_summary}")
        return cached, query_summary, True

    # ── Run searches and merge results ──
    all_jobs = []
    seen_ids = set()
    per_query_limit = max(10, limit // len(unique_queries))

    for q in unique_queries:
        try:
            results = await search_adzuna(q, location, per_query_limit, country)
            for job in results:
                if job["id"] not in seen_ids:
                    seen_ids.add(job["id"])
                    all_jobs.append(job)
        except JobSearchError as e:
            log.warning(f"Search failed for query '{q}': {e}")
            continue

    # Trim to requested limit
    all_jobs = all_jobs[:limit]

    # Cache merged results
    if all_jobs:
        await cache.set(cache_key, all_jobs, ttl=JOB_CACHE_TTL)

    log.info(
        f"Multi-search complete: {len(unique_queries)} queries -> "
        f"{len(all_jobs)} unique jobs"
    )

    return all_jobs, query_summary, False


def _clean_query_term(term: str) -> str:
    """
    Strip parenthetical details and noise from a term.
    'Python (pandas, numpy)' -> 'Python'
    'Java (Basic)' -> 'Java'
    'Machine Learning/AI' -> 'Machine Learning AI'
    """
    import re
    # Remove parenthetical content
    term = re.sub(r"\([^)]*\)", "", term)
    # Remove slashes (Adzuna treats them as literal)
    term = term.replace("/", " ")
    # Collapse whitespace
    term = re.sub(r"\s+", " ", term).strip()
    return term


def _clean_skill_list(skills: list[str]) -> list[str]:
    """
    Clean and simplify skills for search queries.
    Removes parenthetical qualifiers, very short/generic terms.
    """
    cleaned = []
    skip_terms = {"basic", "advanced", "intermediate", "proficient", "familiar"}

    for skill in skills:
        clean = _clean_query_term(skill)
        # Skip very short or generic terms
        if len(clean) < 2 or clean.lower() in skip_terms:
            continue
        cleaned.append(clean)

    return cleaned