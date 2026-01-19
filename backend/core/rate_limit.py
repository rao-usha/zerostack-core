"""Rate limiting configuration for API endpoints."""
import logging
from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


def get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key from request.

    Uses IP address by default, but can be extended to use
    user ID when authentication is implemented.
    """
    # TODO: When auth is implemented, use user ID if available
    # user = getattr(request.state, "user", None)
    # if user:
    #     return f"user:{user.id}"
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["200/minute"],  # Default for all endpoints
    storage_uri="memory://",  # Use Redis in production: "redis://localhost:6379"
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom handler for rate limit exceeded errors."""
    logger.warning(f"Rate limit exceeded for {get_rate_limit_key(request)}: {exc.detail}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": f"Too many requests. {exc.detail}",
            "retry_after": getattr(exc, "retry_after", 60),
        },
    )


# Pre-defined rate limit decorators for common use cases
def limit_chat(func: Callable) -> Callable:
    """Rate limit for chat/LLM endpoints (20/minute)."""
    return limiter.limit("20/minute")(func)


def limit_generation(func: Callable) -> Callable:
    """Rate limit for expensive generation endpoints (5/minute)."""
    return limiter.limit("5/minute")(func)


def limit_standard(func: Callable) -> Callable:
    """Standard rate limit (100/minute)."""
    return limiter.limit("100/minute")(func)


def limit_burst(func: Callable) -> Callable:
    """Allow short bursts (300/minute)."""
    return limiter.limit("300/minute")(func)
