"""
Rate limiting middleware using slowapi.
Configurable per-minute limits from environment.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from config import get_settings

settings = get_settings()

# Rate limiter keyed by client IP
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)
