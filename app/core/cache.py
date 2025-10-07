"""
Shared caching utilities for API clients.

Provides file-based caching with TTL (time-to-live) support for external API responses.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)


def get_cache_dir(service_name: str) -> Path:
    """
    Get the cache directory for a specific service.

    Creates the directory if it doesn't exist.

    Args:
        service_name: Name of the service (e.g., 'fred', 'hud', 'census')

    Returns:
        Path to the cache directory
    """
    # Get project root (2 levels up from this file)
    project_root = Path(__file__).parent.parent.parent
    cache_dir = project_root / "data" / "cache" / service_name
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def generate_cache_key(*args: Any) -> str:
    """
    Generate a cache key from arguments.

    Creates a hash of the arguments to use as a filename-safe cache key.

    Args:
        *args: Arguments to hash

    Returns:
        SHA256 hash of the arguments
    """
    # Convert args to a stable string representation
    key_string = json.dumps(args, sort_keys=True, default=str)
    return hashlib.sha256(key_string.encode()).hexdigest()


def save_to_cache(
    service_name: str,
    cache_key: str,
    data: Any,
    metadata: Optional[dict] = None
) -> None:
    """
    Save data to cache with metadata.

    Args:
        service_name: Name of the service
        cache_key: Unique cache key
        data: Data to cache (must be JSON serializable)
        metadata: Optional metadata to store alongside data
    """
    cache_dir = get_cache_dir(service_name)
    cache_file = cache_dir / f"{cache_key}.json"

    cache_obj = {
        "cached_at": datetime.now().isoformat(),
        "metadata": metadata or {},
        "data": data
    }

    try:
        with open(cache_file, "w") as f:
            json.dump(cache_obj, f, indent=2, default=str)
        logger.debug(
            f"Saved to cache",
            extra={
                "service": service_name,
                "cache_key": cache_key,
                "file": str(cache_file)
            }
        )
    except Exception as e:
        logger.warning(
            f"Failed to save to cache: {e}",
            extra={"service": service_name, "cache_key": cache_key}
        )


def load_from_cache(
    service_name: str,
    cache_key: str,
    ttl_hours: int = 24
) -> Optional[dict]:
    """
    Load data from cache if it exists and is not expired.

    Args:
        service_name: Name of the service
        cache_key: Unique cache key
        ttl_hours: Time-to-live in hours (default: 24)

    Returns:
        Cache object with 'cached_at', 'metadata', and 'data' keys,
        or None if cache miss or expired
    """
    cache_dir = get_cache_dir(service_name)
    cache_file = cache_dir / f"{cache_key}.json"

    if not cache_file.exists():
        logger.debug(
            f"Cache miss - file not found",
            extra={"service": service_name, "cache_key": cache_key}
        )
        return None

    try:
        with open(cache_file, "r") as f:
            cache_obj = json.load(f)

        # Check if cache is expired
        cached_at = datetime.fromisoformat(cache_obj["cached_at"])
        expiry_time = cached_at + timedelta(hours=ttl_hours)

        if datetime.now() > expiry_time:
            logger.debug(
                f"Cache expired",
                extra={
                    "service": service_name,
                    "cache_key": cache_key,
                    "cached_at": cache_obj["cached_at"],
                    "ttl_hours": ttl_hours
                }
            )
            return None

        logger.debug(
            f"Cache hit",
            extra={
                "service": service_name,
                "cache_key": cache_key,
                "cached_at": cache_obj["cached_at"]
            }
        )
        return cache_obj

    except Exception as e:
        logger.warning(
            f"Failed to load from cache: {e}",
            extra={"service": service_name, "cache_key": cache_key}
        )
        return None


def cleanup_expired_cache(service_name: str, ttl_hours: int = 24) -> int:
    """
    Remove expired cache files for a service.

    Args:
        service_name: Name of the service
        ttl_hours: Time-to-live in hours

    Returns:
        Number of files removed
    """
    cache_dir = get_cache_dir(service_name)
    removed_count = 0

    for cache_file in cache_dir.glob("*.json"):
        try:
            with open(cache_file, "r") as f:
                cache_obj = json.load(f)

            cached_at = datetime.fromisoformat(cache_obj["cached_at"])
            expiry_time = cached_at + timedelta(hours=ttl_hours)

            if datetime.now() > expiry_time:
                cache_file.unlink()
                removed_count += 1
                logger.debug(
                    f"Removed expired cache file",
                    extra={"service": service_name, "file": str(cache_file)}
                )

        except Exception as e:
            logger.warning(
                f"Failed to check/remove cache file {cache_file}: {e}",
                extra={"service": service_name}
            )

    if removed_count > 0:
        logger.info(
            f"Cleaned up expired cache files",
            extra={"service": service_name, "count": removed_count}
        )

    return removed_count


def clear_cache(service_name: str) -> int:
    """
    Clear all cache files for a service.

    Args:
        service_name: Name of the service

    Returns:
        Number of files removed
    """
    cache_dir = get_cache_dir(service_name)
    removed_count = 0

    for cache_file in cache_dir.glob("*.json"):
        try:
            cache_file.unlink()
            removed_count += 1
        except Exception as e:
            logger.warning(
                f"Failed to remove cache file {cache_file}: {e}",
                extra={"service": service_name}
            )

    logger.info(
        f"Cleared cache",
        extra={"service": service_name, "count": removed_count}
    )

    return removed_count
