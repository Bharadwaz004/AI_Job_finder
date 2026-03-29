"""
AI Resume Job Finder — FastAPI Application Entry Point

Registers routes, middleware, exception handlers, and lifecycle events.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import get_settings
from database import connect_db, close_db
from routes import resume_router, jobs_router, ranking_router
from utils.rate_limiter import limiter
from utils.exceptions import AppException, global_exception_handler
from utils.logger import setup_logger

log = setup_logger("main")
settings = get_settings()


# ══════════════════════════════════════════════
#  Lifecycle (startup / shutdown)
# ══════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting AI Resume Job Finder...")
    await connect_db()
    yield
    await close_db()
    log.info("Shutdown complete.")


# ══════════════════════════════════════════════
#  App Factory
# ══════════════════════════════════════════════

app = FastAPI(
    title="AI Resume Job Finder",
    description="Upload your resume, get matched with relevant jobs, and see skill gaps",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate limiter ──
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler ──
app.add_exception_handler(AppException, global_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


# ══════════════════════════════════════════════
#  Request logging middleware
# ══════════════════════════════════════════════

@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000

    log.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration:.0f}ms)"
    )
    return response


# ══════════════════════════════════════════════
#  Routes
# ══════════════════════════════════════════════

app.include_router(resume_router)
app.include_router(jobs_router)
app.include_router(ranking_router)


@app.get("/", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Resume Job Finder",
        "version": "1.0.0",
    }


@app.get("/api/health", tags=["Health"])
async def api_health():
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "llm_model": settings.hf_model if settings.llm_provider == "huggingface" else settings.ollama_model,
    }


# ══════════════════════════════════════════════
#  Run directly
# ══════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level="info",
    )