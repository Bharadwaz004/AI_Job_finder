"""
Resume routes: upload, parse, extract profile.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Request

from config import get_settings
from database import get_db
from services.resume_parser import validate_file, extract_text
from services.llm_service import parse_resume_with_llm
from models.schemas import ResumeUploadResponse, ProfileResponse, ExtractedProfile
from utils.logger import setup_logger
from utils.rate_limiter import limiter
from utils.exceptions import FileValidationError, NotFoundError

log = setup_logger("routes.resume")
router = APIRouter(prefix="/api", tags=["Resume"])


@router.post("/upload-resume", response_model=ResumeUploadResponse)
@limiter.limit("10/minute")
async def upload_resume(request: Request, file: UploadFile = File(...)):
    """
    Upload a resume (PDF/DOCX), extract text, store in DB.
    Returns resume ID for subsequent operations.
    """
    settings = get_settings()

    # Read file content
    content = await file.read()

    # Validate
    validate_file(
        filename=file.filename,
        content_type=file.content_type,
        size=len(content),
        max_size=settings.max_upload_bytes,
    )

    # Extract text
    text = await extract_text(content, file.filename)

    # Save to DB
    resume_id = uuid.uuid4().hex[:16]
    db = get_db()
    await db.resumes.insert_one({
        "_id": resume_id,
        "filename": file.filename,
        "text": text,
        "raw_size": len(content),
        "created_at": datetime.utcnow().isoformat(),
    })

    # Optionally save file to disk
    try:
        filepath = settings.upload_path / f"{resume_id}_{file.filename}"
        with open(filepath, "wb") as f:
            f.write(content)
    except Exception as e:
        log.warning(f"Could not save file to disk: {e}")

    log.info(f"Resume uploaded: {resume_id} ({file.filename}, {len(content)} bytes)")
    return ResumeUploadResponse(id=resume_id, filename=file.filename)


@router.post("/extract-profile", response_model=ProfileResponse)
@limiter.limit("10/minute")
async def extract_profile(request: Request, resume_id: str):
    """
    Parse a previously uploaded resume using LLM.
    Extracts structured profile: skills, experience, projects, suggested roles.
    """
    db = get_db()
    resume = await db.resumes.find_one({"_id": resume_id})

    if not resume:
        raise NotFoundError(f"Resume not found: {resume_id}")

    # LLM extraction
    parsed = await parse_resume_with_llm(resume["text"])
    profile = ExtractedProfile(**parsed)

    # Store profile
    profile_id = uuid.uuid4().hex[:16]
    profile_doc = {
        "_id": profile_id,
        "resume_id": resume_id,
        "profile": profile.model_dump(),
        "created_at": datetime.utcnow().isoformat(),
    }
    await db.profiles.insert_one(profile_doc)

    log.info(f"Profile extracted: {profile_id} | Skills: {len(profile.skills)} | Roles: {profile.suggested_roles}")

    return ProfileResponse(
        id=profile_id,
        resume_id=resume_id,
        profile=profile,
    )


@router.get("/profile/{profile_id}")
@limiter.limit("30/minute")
async def get_profile(request: Request, profile_id: str):
    """Retrieve a previously extracted profile."""
    db = get_db()
    doc = await db.profiles.find_one({"_id": profile_id})

    if not doc:
        raise NotFoundError(f"Profile not found: {profile_id}")

    return {
        "id": doc["_id"],
        "resume_id": doc["resume_id"],
        "profile": doc["profile"],
        "created_at": doc.get("created_at"),
    }
