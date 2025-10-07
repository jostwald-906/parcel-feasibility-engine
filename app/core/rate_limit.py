"""
Rate limiting configuration for API endpoints.

Uses SlowAPI for FastAPI-native rate limiting to protect against:
- API abuse and excessive requests
- Costly Railway usage charges
- GIS service rate limits

Rate limiting is applied per IP address by default.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/hour"],  # Default: 100 requests per hour per IP
    storage_uri="memory://",
    enabled=settings.RATE_LIMIT_ENABLED,
)

# Custom rate limit decorators for different endpoint types
RATE_LIMITS = {
    "analysis": "10/minute",      # Heavy endpoint: 10 per minute
    "pdf_export": "5/minute",     # Very heavy: 5 per minute
    "autocomplete": "30/minute",  # Light endpoint: 30 per minute
    "metadata": "50/minute",      # Very light: 50 per minute
}


def get_user_or_ip(request):
    """
    Get rate limit key from authenticated user if available, otherwise IP.

    This allows for user-based rate limiting when authentication is added.
    Currently falls back to IP-based limiting.
    """
    # Check for authenticated user (future implementation)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Fall back to IP address
    return get_remote_address(request)
