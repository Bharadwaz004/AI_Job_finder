"""
Pydantic schemas for request/response validation.
These serve as the contract between frontend, backend, and database.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ═══════════════════════════════════════════
#  Resume & Profile
# ═══════════════════════════════════════════

class ExtractedProfile(BaseModel):
    """Structured data extracted from resume by LLM."""
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[dict] = Field(
        default_factory=list,
        description="List of {title, company, duration, description}",
    )
    education: list[dict] = Field(
        default_factory=list,
        description="List of {degree, institution, year}",
    )
    projects: list[dict] = Field(
        default_factory=list,
        description="List of {name, description, tech_stack}",
    )
    certifications: list[str] = Field(default_factory=list)
    suggested_roles: list[str] = Field(
        default_factory=list,
        description="Job roles the candidate is best suited for",
    )
    years_of_experience: float = 0.0


class ResumeUploadResponse(BaseModel):
    id: str
    filename: str
    message: str = "Resume uploaded successfully"


class ProfileResponse(BaseModel):
    id: str
    resume_id: str
    profile: ExtractedProfile
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════
#  Jobs
# ═══════════════════════════════════════════

class JobListing(BaseModel):
    """A single job result from search APIs."""
    id: str = ""
    title: str
    company: str
    location: str = ""
    description: str = ""
    link: str = ""
    source: str = ""  # "adzuna", "mock", etc.
    posted_date: str = ""
    salary: str = ""


class JobSearchRequest(BaseModel):
    skills: list[str] = Field(..., min_length=1)
    roles: list[str] = Field(default_factory=list)
    location: str = ""
    country: str = Field(default="", description="Adzuna country code: gb, us, in, de, fr, au, etc.")
    limit: int = Field(default=20, ge=1, le=50)


class JobSearchResponse(BaseModel):
    query_used: str
    total: int
    jobs: list[JobListing]
    cached: bool = False


# ═══════════════════════════════════════════
#  Ranking
# ═══════════════════════════════════════════

class RankingMethod(str, Enum):
    RULE_BASED = "rule_based"
    LLM_BASED = "llm_based"
    HYBRID = "hybrid"


class RankedJob(BaseModel):
    """Job listing augmented with match scoring."""
    job: JobListing
    match_score: float = Field(..., ge=0, le=100, description="0-100 relevance score")
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    explanation: str = ""
    improvement_tips: list[str] = Field(default_factory=list)


class RankJobsRequest(BaseModel):
    profile_id: str
    job_ids: list[str] = Field(default_factory=list, description="If empty, ranks all recent jobs")
    method: RankingMethod = RankingMethod.HYBRID


class RankJobsResponse(BaseModel):
    profile_id: str
    method: str
    ranked_jobs: list[RankedJob]
    skill_gap_summary: dict = Field(
        default_factory=dict,
        description="Aggregate missing skills across all jobs",
    )


# ═══════════════════════════════════════════
#  Skill Gap Analysis
# ═══════════════════════════════════════════

class SkillGapAnalysis(BaseModel):
    most_demanded_skills: list[str] = Field(default_factory=list)
    user_has: list[str] = Field(default_factory=list)
    user_missing: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════
#  Error Response
# ═══════════════════════════════════════════

class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: dict = Field(default_factory=dict)