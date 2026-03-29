"""
Centralized configuration — all settings loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    # ── LLM ──
    llm_provider: str = "huggingface"  # "huggingface" | "ollama"
    hf_api_token: str = ""
    hf_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    # Other strong free options:
    #   "Qwen/Qwen2.5-72B-Instruct"            (best quality, via SambaNova)
    #   "meta-llama/Llama-3.3-70B-Instruct"     (excellent, via Cerebras)
    #   "deepseek-ai/DeepSeek-V3-0324"          (very strong reasoning)
    #   "mistralai/Mistral-Small-24B-Instruct-2501"
    hf_api_url: str = "https://router.huggingface.co/v1"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"

    # ── Job Search (Adzuna) ──
    # Register free at: https://developer.adzuna.com/
    adzuna_app_id: str = "fada6711"
    adzuna_app_key: str = "369048d2e5eca8317b04d557baf79fc8"
    adzuna_country: str = "in"  # gb, us, de, fr, au, in, ca, etc.

    # ── MongoDB ──
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "resume_job_finder"

    # ── Redis ──
    redis_url: str = ""

    # ── App ──
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10
    frontend_url: str = "http://localhost:5173"

    # ── Rate Limiting ──
    rate_limit_per_minute: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache()
def get_settings() -> Settings:
    return Settings()