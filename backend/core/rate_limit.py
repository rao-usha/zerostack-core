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

    Uses authenticated user ID if available, falls back to IP address.
    This provides fairer rate limiting for authenticated users across
    different IPs (mobile, VPN, etc.) while still limiting anonymous requests.
    """
    # Try to get user from request state (set by auth middleware)
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return f"user:{user.id}"

    # Check for JWT token in Authorization header and extract user ID
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from core.jwt import decode_token
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            if payload and "sub" in payload:
                return f"user:{payload['sub']}"
        except Exception:
            pass  # Invalid token, fall back to IP

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
