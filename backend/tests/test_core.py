"""
Unit tests for core backend functionality.
All external services (LLM, job search, DB) are mocked.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

# ── Resume Parser Tests ──

class TestResumeValidation:
    def test_valid_pdf(self):
        from services.resume_parser import validate_file
        # Should not raise
        validate_file("resume.pdf", "application/pdf", 1024, 10 * 1024 * 1024)

    def test_valid_docx(self):
        from services.resume_parser import validate_file
        validate_file(
            "resume.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            2048,
            10 * 1024 * 1024,
        )

    def test_invalid_extension(self):
        from services.resume_parser import validate_file
        from utils.exceptions import FileValidationError
        with pytest.raises(FileValidationError, match="Unsupported file type"):
            validate_file("resume.txt", "text/plain", 1024, 10 * 1024 * 1024)

    def test_file_too_large(self):
        from services.resume_parser import validate_file
        from utils.exceptions import FileValidationError
        with pytest.raises(FileValidationError, match="File too large"):
            validate_file("resume.pdf", "application/pdf", 20 * 1024 * 1024, 10 * 1024 * 1024)


# ── LLM JSON Extraction Tests ──

class TestJSONExtraction:
    def test_clean_json(self):
        from services.llm_service import extract_json
        result = extract_json('{"name": "John", "skills": ["Python"]}')
        assert result["name"] == "John"

    def test_json_with_markdown_fences(self):
        from services.llm_service import extract_json
        raw = '```json\n{"name": "Jane"}\n```'
        result = extract_json(raw)
        assert result["name"] == "Jane"

    def test_json_with_preamble(self):
        from services.llm_service import extract_json
        raw = 'Here is the extracted data:\n{"name": "Bob", "skills": []}'
        result = extract_json(raw)
        assert result["name"] == "Bob"

    def test_json_with_trailing_comma(self):
        from services.llm_service import extract_json
        raw = '{"name": "Alice", "skills": ["Python", "React",]}'
        result = extract_json(raw)
        assert result["name"] == "Alice"

    def test_invalid_json_raises(self):
        from services.llm_service import extract_json
        from utils.exceptions import LLMError
        with pytest.raises(LLMError):
            extract_json("this is not json at all")


# ── Ranking Tests ──

class TestRuleBasedScoring:
    def test_high_match(self):
        from services.ranking import rule_based_score

        profile = {
            "skills": ["python", "react", "sql", "docker", "aws"],
            "suggested_roles": ["Software Engineer"],
            "years_of_experience": 4,
        }
        job = {
            "title": "Senior Software Engineer",
            "description": "Looking for a Python developer with React, SQL, Docker, and AWS experience.",
        }

        result = rule_based_score(profile, job)
        assert result["match_score"] > 60
        assert len(result["matched_skills"]) > 0

    def test_low_match(self):
        from services.ranking import rule_based_score

        profile = {
            "skills": ["painting", "drawing", "sculpture"],
            "suggested_roles": ["Artist"],
            "years_of_experience": 10,
        }
        job = {
            "title": "Backend Engineer",
            "description": "Python, Django, PostgreSQL, Docker, Kubernetes required.",
        }

        result = rule_based_score(profile, job)
        assert result["match_score"] < 50
        assert len(result["missing_skills"]) > 0

    def test_empty_skills(self):
        from services.ranking import rule_based_score
        profile = {"skills": [], "suggested_roles": [], "years_of_experience": 0}
        job = {"title": "Developer", "description": "Python needed"}

        result = rule_based_score(profile, job)
        assert 0 <= result["match_score"] <= 100


# ── Cache Tests ──

@pytest.mark.asyncio
class TestInMemoryCache:
    async def test_set_and_get(self):
        from utils.cache import InMemoryCache
        cache = InMemoryCache()
        await cache.set("key1", {"data": "test"}, ttl=60)
        result = await cache.get("key1")
        assert result == {"data": "test"}

    async def test_cache_miss(self):
        from utils.cache import InMemoryCache
        cache = InMemoryCache()
        result = await cache.get("nonexistent")
        assert result is None

    async def test_cache_key_generation(self):
        from utils.cache import make_cache_key
        key1 = make_cache_key("jobs", "python developer", "india")
        key2 = make_cache_key("jobs", "python developer", "india")
        key3 = make_cache_key("jobs", "java developer", "india")
        assert key1 == key2  # Same input → same key
        assert key1 != key3  # Different input → different key
