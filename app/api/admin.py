"""
Admin API endpoints.

Provides administrative functionality for cache management, system monitoring,
and operations support.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.services.gis_service import clear_gis_cache, get_cache_stats

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/cache/clear")
async def clear_cache() -> Dict[str, str]:
    """
    Clear all GIS caches.

    This endpoint clears both the manual TTL cache and the functools.lru_cache.
    Useful for:
    - Testing cache behavior
    - Forcing fresh data fetch
    - Resolving stale data issues

    Returns:
        Success message

    Example:
        POST /api/v1/admin/cache/clear
        Response: {"message": "GIS cache cleared successfully", "parcels_cleared": 42}
    """
    try:
        # Get stats before clearing
        stats_before = get_cache_stats()
        parcels_cleared = stats_before["cached_parcels"]

        # Clear cache
        clear_gis_cache()

        logger.info(f"Admin cleared GIS cache ({parcels_cleared} parcels)")

        return {
            "message": "GIS cache cleared successfully",
            "parcels_cleared": parcels_cleared,
        }
    except Exception as e:
        logger.error(f"Failed to clear GIS cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/cache/stats")
async def get_cache_statistics() -> Dict[str, Any]:
    """
    Get cache statistics.

    Returns detailed metrics about the GIS cache including:
    - Number of cached parcels
    - Maximum cache size
    - TTL configuration
    - Cache hit/miss counts
    - Hit rate percentage

    Returns:
        Cache statistics dict

    Example:
        GET /api/v1/admin/cache/stats
        Response:
        {
            "cached_parcels": 42,
            "max_size": 1000,
            "ttl_hours": 24,
            "cache_hits": 156,
            "cache_misses": 42,
            "hit_rate_pct": 78.79
        }
    """
    try:
        stats = get_cache_stats()
        logger.debug(f"Cache stats requested: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache statistics")


@router.get("/health")
async def admin_health_check() -> Dict[str, Any]:
    """
    Detailed health check for administrative monitoring.

    Returns comprehensive system health including:
    - Cache statistics
    - Configuration status
    - Service availability

    Returns:
        Detailed health status dict

    Example:
        GET /api/v1/admin/health
        Response:
        {
            "status": "healthy",
            "cache": {...},
            "services": {...}
        }
    """
    from app.core.config import settings

    try:
        cache_stats = get_cache_stats()

        return {
            "status": "healthy",
            "cache": cache_stats,
            "services": {
                "gis_configured": bool(settings.SANTA_MONICA_PARCEL_SERVICE_URL),
                "gis_timeout": settings.GIS_REQUEST_TIMEOUT,
                "cache_enabled": True,
            },
            "config": {
                "environment": settings.ENVIRONMENT,
                "log_level": settings.LOG_LEVEL,
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
