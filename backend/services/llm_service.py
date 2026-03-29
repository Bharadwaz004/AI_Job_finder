"""
LLM service for structured resume parsing and job scoring.
Supports HuggingFace Inference API (free tier) and Ollama (local models).
Includes robust JSON extraction with retry logic and HF-specific error handling.
"""

import json
import re

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from utils.logger import setup_logger
from utils.exceptions import LLMError

log = setup_logger("llm_service")

# ══════════════════════════════════════════════
#  Prompts
# ══════════════════════════════════════════════

RESUME_PARSE_PROMPT = """You are an expert resume parser. Analyze the following resume text and extract structured information.

CRITICAL INSTRUCTIONS:
- Return ONLY a valid JSON object
- Do NOT include any text before or after the JSON
- Do NOT wrap the JSON in markdown code fences
- All string values must be properly escaped

Return this exact JSON schema:
{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "+1234567890",
  "location": "City, Country",
  "summary": "Brief professional summary in 1-2 sentences",
  "skills": ["skill1", "skill2"],
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "duration": "Jan 2020 - Dec 2022",
      "description": "Brief description of role"
    }}
  ],
  "education": [
    {{
      "degree": "B.Tech in Computer Science",
      "institution": "University Name",
      "year": "2019"
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "description": "What it does",
      "tech_stack": ["Python", "React"]
    }}
  ],
  "certifications": ["cert1", "cert2"],
  "suggested_roles": ["Software Engineer", "Data Analyst"],
  "years_of_experience": 3.5
}}

RESUME TEXT:
{resume_text}

JSON:"""

JOB_SCORE_PROMPT = """You are a career advisor. Score how well this candidate matches the job.

CANDIDATE PROFILE:
- Skills: {skills}
- Experience: {experience_summary}
- Years of experience: {years}

JOB:
- Title: {job_title}
- Company: {company}
- Description: {job_description}

CRITICAL: Return ONLY valid JSON, no other text, no markdown fences.
{{
  "match_score": 75,
  "matched_skills": ["Python", "SQL"],
  "missing_skills": ["Kubernetes", "Go"],
  "explanation": "Strong match because...",
  "improvement_tips": ["Learn Kubernetes for container orchestration"]
}}

JSON:"""


# ══════════════════════════════════════════════
#  JSON Extraction (handles LLM quirks)
# ══════════════════════════════════════════════

def extract_json(text: str) -> dict:
    """
    Robustly extract JSON from LLM output.
    Handles: markdown fences, preamble text, trailing commas,
    repeated JSON (HF models sometimes echo), text after JSON.
    """
    # Strip markdown code fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find the FIRST complete JSON object (HF models sometimes output multiple)
    brace_depth = 0
    start = text.find("{")
    if start == -1:
        raise LLMError(f"No JSON object found in LLM response. Raw output: {text[:500]}")

    for i in range(start, len(text)):
        if text[i] == "{":
            brace_depth += 1
        elif text[i] == "}":
            brace_depth -= 1
            if brace_depth == 0:
                candidate = text[start:i + 1]
                # Remove trailing commas before closing braces/brackets
                candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
                # Fix common HF quirk: single quotes instead of double
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    # Try replacing single quotes (risky but sometimes needed)
                    try:
                        fixed = candidate.replace("'", '"')
                        return json.loads(fixed)
                    except json.JSONDecodeError:
                        pass
                break

    # Last resort: try the whole region from first { to last }
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        candidate = text[start:end]
        candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise LLMError(f"Could not extract valid JSON from LLM response. Raw output: {text[:500]}")


# ══════════════════════════════════════════════
#  LLM Providers
# ══════════════════════════════════════════════

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=2, max=30),
    retry=lambda retry_state: _should_retry_hf(retry_state),
)
async def call_huggingface(prompt: str, system: str = "You are a helpful assistant.") -> str:
    """
    Call HuggingFace Inference Providers via the OpenAI-compatible router.
    
    Base URL: https://router.huggingface.co/v1
    The router auto-selects the fastest provider (Cerebras, SambaNova, Together, etc.)
    
    Recommended models (all free tier):
      - meta-llama/Llama-3.1-8B-Instruct          (fast, reliable)
      - Qwen/Qwen2.5-72B-Instruct                 (best quality, via SambaNova)
      - meta-llama/Llama-3.3-70B-Instruct          (excellent, via Cerebras)
      - deepseek-ai/DeepSeek-V3-0324               (strong reasoning)
      - mistralai/Mistral-Small-24B-Instruct-2501  (good balance)
    
    Token needs "Make calls to Inference Providers" permission.
    Create at: https://huggingface.co/settings/tokens
    """
    settings = get_settings()

    if not settings.hf_api_token:
        raise LLMError(
            "HuggingFace API token not configured. "
            "Get a free token at https://huggingface.co/settings/tokens "
            "(enable 'Make calls to Inference Providers' permission) "
            "and set HF_API_TOKEN in .env"
        )

    # POST to the unified router — model goes in the JSON body, NOT in the URL
    url = f"{settings.hf_api_url}/chat/completions"

    log.info(f"HF request -> {url} | model={settings.hf_model}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.hf_api_token}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.hf_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 4000,
                "stream": False,
            },
        )

        # Handle HF-specific status codes
        if response.status_code == 503:
            # Model is loading or provider unavailable
            try:
                body = response.json()
                wait_time = body.get("estimated_time", 30)
                error_msg = body.get("error", "Model loading")
            except Exception:
                wait_time = 30
                error_msg = "Service unavailable"
            log.warning(f"HF 503: {error_msg} (estimated wait: {wait_time}s) — retrying...")
            raise LLMError(f"Model unavailable: {error_msg} (estimated {wait_time}s)")

        if response.status_code == 429:
            log.warning("HF rate limit hit — retrying with backoff...")
            raise LLMError("HuggingFace rate limit exceeded")

        if response.status_code == 422:
            error_body = response.text[:500]
            log.error(f"HF 422 (validation error): {error_body}")
            raise LLMError(f"HuggingFace rejected the request: {error_body}")

        if response.status_code != 200:
            error_body = response.text[:500]
            log.error(f"HuggingFace API error {response.status_code}: {error_body}")
            raise LLMError(f"HuggingFace API returned status {response.status_code}: {error_body}")

        data = response.json()
        log.info(f"HF response keys: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}")

        # Parse response — OpenAI-compatible format
        try:
            content = data["choices"][0]["message"]["content"]
            if not content or not content.strip():
                raise LLMError("HuggingFace returned empty response content")
            return content
        except (KeyError, IndexError, TypeError) as e:
            # Fallback: some models return in legacy format
            if isinstance(data, list) and len(data) > 0:
                text = data[0].get("generated_text", "")
                if text:
                    return text
            log.error(f"Unexpected HF response format ({e}): {json.dumps(data)[:500]}")
            raise LLMError(f"Unexpected response format from HuggingFace API: {e}")


def _should_retry_hf(retry_state) -> bool:
    """Retry on 503 (model loading) and 429 (rate limit), not on auth/validation errors."""
    exc = retry_state.outcome.exception()
    if exc is None:
        return False
    msg = str(exc).lower()
    # Don't retry auth failures, not-found, or validation errors
    if any(code in msg for code in ["401", "403", "404", "422"]):
        return False
    return True


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def call_ollama(prompt: str, system: str = "You are a helpful assistant.") -> str:
    """Call local Ollama API (fallback for offline development)."""
    settings = get_settings()

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "system": system,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1},
            },
        )

        if response.status_code != 200:
            raise LLMError(f"Ollama API returned status {response.status_code}")

        return response.json()["response"]


async def call_llm(prompt: str, system: str = "You are a helpful assistant.") -> str:
    """Route to configured LLM provider."""
    settings = get_settings()
    provider = settings.llm_provider.lower()

    log.info(f"Calling LLM provider: {provider} | model: {settings.hf_model if provider == 'huggingface' else settings.ollama_model}")

    if provider == "huggingface":
        return await call_huggingface(prompt, system)
    elif provider == "ollama":
        return await call_ollama(prompt, system)
    else:
        raise LLMError(f"Unknown LLM provider: '{provider}'. Use 'huggingface' or 'ollama'.")


# ══════════════════════════════════════════════
#  Public API
# ══════════════════════════════════════════════

async def parse_resume_with_llm(resume_text: str) -> dict:
    """
    Send resume text to LLM and extract structured profile data.
    Returns validated dict matching ExtractedProfile schema.
    """
    # Truncate for HF model context windows (7B models ~8K tokens)
    if len(resume_text) > 8000:
        log.warning("Resume text truncated to 8000 chars for LLM context window")
        resume_text = resume_text[:8000]

    prompt = RESUME_PARSE_PROMPT.format(resume_text=resume_text)
    system = (
        "You are an expert resume parser. You MUST return ONLY a valid JSON object. "
        "Do NOT include any explanation, commentary, or markdown formatting. "
        "Start your response with { and end with }. Nothing else."
    )

    raw = await call_llm(prompt, system)
    log.info(f"LLM resume parse response length: {len(raw)} chars")

    parsed = extract_json(raw)

    # Ensure required fields have defaults
    defaults = {
        "name": "", "email": "", "phone": "", "location": "",
        "summary": "", "skills": [], "experience": [], "education": [],
        "projects": [], "certifications": [], "suggested_roles": [],
        "years_of_experience": 0.0,
    }
    for key, default in defaults.items():
        if key not in parsed:
            parsed[key] = default

    return parsed


async def score_job_with_llm(profile: dict, job: dict) -> dict:
    """
    Use LLM to score a job against a candidate profile.
    Returns match_score, matched/missing skills, explanation.
    Always returns a dict with correct types regardless of LLM output.
    """
    # Build experience summary
    exp_lines = []
    for exp in profile.get("experience", [])[:3]:
        exp_lines.append(f"- {exp.get('title', '')} at {exp.get('company', '')}")
    experience_summary = "\n".join(exp_lines) if exp_lines else "Not specified"

    prompt = JOB_SCORE_PROMPT.format(
        skills=", ".join(profile.get("skills", [])),
        experience_summary=experience_summary,
        years=profile.get("years_of_experience", 0),
        job_title=job.get("title", ""),
        company=job.get("company", ""),
        job_description=job.get("description", "")[:2000],
    )

    raw = await call_llm(
        prompt,
        "You are a career advisor. Return ONLY a valid JSON object. "
        "Start with { and end with }. No other text."
    )
    parsed = extract_json(raw)

    # ── Normalize output types (LLMs return unpredictable types) ──

    # Score: must be float 0-100
    try:
        score = float(parsed.get("match_score", 50))
    except (TypeError, ValueError):
        score = 50.0

    # Lists: ensure these are lists, not strings
    matched = parsed.get("matched_skills", [])
    if isinstance(matched, str):
        matched = [s.strip() for s in matched.split(",") if s.strip()]

    missing = parsed.get("missing_skills", [])
    if isinstance(missing, str):
        missing = [s.strip() for s in missing.split(",") if s.strip()]

    tips = parsed.get("improvement_tips", [])
    if isinstance(tips, str):
        tips = [s.strip() for s in tips.split(",") if s.strip()]

    # Explanation: must be string
    explanation = parsed.get("explanation", "")
    if not isinstance(explanation, str):
        explanation = str(explanation)

    return {
        "match_score": max(0, min(100, score)),
        "matched_skills": matched,
        "missing_skills": missing,
        "explanation": explanation,
        "improvement_tips": tips,
    }