"""
Custom exceptions with structured error responses.
Global exception handler registered in main.py.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from utils.logger import setup_logger

log = setup_logger("exceptions")


# ── Custom Exceptions ──

class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = 500, detail: dict = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(message)


class FileValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class ResumeParsingError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class LLMError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=502)


class JobSearchError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=502)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


# ── Global Handler ──

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches all unhandled exceptions and returns structured JSON."""

    if isinstance(exc, AppException):
        log.error(f"{exc.__class__.__name__}: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    # Unexpected errors
    log.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again.",
        },
    )
