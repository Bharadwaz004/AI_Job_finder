"""
Ranking service: score and rank jobs against candidate profiles.
"""

import re
from collections import Counter
from typing import List, Dict, Any
from utils.logger import setup_logger
from services.llm_service import score_job_with_llm

log = setup_logger("services.ranking")


def rule_based_score(profile: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rule-based scoring: keyword overlap + role matching + experience.
    """
    profile_skills = set(s.lower() for s in profile.get("skills", []))
    profile_roles = set(r.lower() for r in profile.get("suggested_roles", []))
    experience = profile.get("years_of_experience", 0)

    job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    job_skills = extract_skills_from_text(job_text)

    # Skill overlap
    matched_skills = profile_skills & job_skills
    missing_skills = job_skills - profile_skills
    skill_score = len(matched_skills) / max(len(job_skills), 1) * 60

    # Role matching
    role_score = 0
    for role in profile_roles:
        if role in job_text:
            role_score = 20
            break

    # Experience bonus
    exp_score = min(experience * 2, 20)

    total_score = skill_score + role_score + exp_score

    return {
        "match_score": min(total_score, 100),
        "matched_skills": list(matched_skills),
        "missing_skills": list(missing_skills),
        "explanation": f"Matched {len(matched_skills)} skills, role match: {role_score > 0}, experience: {exp_score}",
        "improvement_tips": [f"Learn {skill}" for skill in list(missing_skills)[:3]],
    }


def extract_skills_from_text(text: str) -> set:
    """
    Extract potential skills from job text (simple keyword extraction).
    """
    # Common tech skills
    skills = {
        "python", "java", "javascript", "react", "angular", "vue", "node", "django", "flask",
        "sql", "mysql", "postgresql", "mongodb", "redis", "docker", "kubernetes", "aws", "azure",
        "git", "linux", "html", "css", "typescript", "c++", "c#", "go", "rust", "php", "ruby",
        "machine learning", "ai", "data science", "tensorflow", "pytorch", "pandas", "numpy",
    }
    found = set()
    for skill in skills:
        if skill in text:
            found.add(skill)
    return found


async def llm_based_score(profile: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """
    LLM-based scoring: use LLM to analyze match.
    """
    try:
        return await score_job_with_llm(profile, job)
    except Exception as e:
        log.error(f"LLM scoring failed: {e}")
        return rule_based_score(profile, job)  # fallback


async def rank_jobs(profile: Dict[str, Any], jobs: List[Dict[str, Any]], method: str) -> tuple:
    """
    Rank jobs using specified method.
    Returns: (ranked_jobs, skill_gap_summary)
    """
    ranked = []

    for job in jobs:
        if method == "rule_based":
            score = rule_based_score(profile, job)
        elif method == "llm_based":
            score = await llm_based_score(profile, job)
        elif method == "hybrid":
            rule_score = rule_based_score(profile, job)
            llm_score = await llm_based_score(profile, job)
            # Average scores
            score = {
                "match_score": (rule_score["match_score"] + llm_score["match_score"]) / 2,
                "matched_skills": list(set(rule_score["matched_skills"] + llm_score["matched_skills"])),
                "missing_skills": list(set(rule_score["missing_skills"] + llm_score["missing_skills"])),
                "explanation": f"Rule: {rule_score['explanation']} | LLM: {llm_score['explanation']}",
                "improvement_tips": list(set(rule_score["improvement_tips"] + llm_score["improvement_tips"])),
            }
        else:
            score = rule_based_score(profile, job)

        ranked.append({
            "job": job,
            **score
        })

    # Sort by match_score descending
    ranked.sort(key=lambda x: x["match_score"], reverse=True)

    # Skill gap summary
    all_missing = Counter()
    for r in ranked[:5]:  # Top 5
        for skill in r["missing_skills"]:
            if isinstance(skill, str) and skill:
                all_missing[skill] += 1

    user_skills = set(profile.get("skills", []))
    most_demanded = [s for s, _ in all_missing.most_common(10)]

    skill_gap = {
        "most_demanded_skills": most_demanded,
        "user_has": list(user_skills),
        "user_missing": [s for s in most_demanded if s.lower() not in {us.lower() for us in user_skills}],
        "recommendations": [
            f"Learn {s} - requested in {c} of {len(jobs)} jobs"
            for s, c in all_missing.most_common(5)
        ],
    }

    return ranked, skill_gap