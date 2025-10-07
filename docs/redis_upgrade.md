# Upgrading to Redis Cache

This guide covers upgrading from the in-memory LRU cache to Redis for multi-instance deployments.

## When to Upgrade

Upgrade to Redis when:

- **Scaling to multiple Railway instances** - In-memory cache doesn't share across instances
- **High cache hit rates** - You're seeing >50% hit rate and want to maximize across all instances
- **Cache persistence needed** - Want cache to survive app restarts
- **Distributed architecture** - Running multiple backend servers behind load balancer

For single-instance deployments, the current LRU cache is sufficient and simpler.

## Current Architecture (LRU Cache)

```
┌─────────────────────┐
│  Railway Instance   │
│                     │
│  ┌──────────────┐  │
│  │  FastAPI App │  │
│  │              │  │
│  │  LRU Cache   │  │
│  │  (In-Memory) │  │
│  └──────────────┘  │
└─────────────────────┘

Pros:
  ✓ No dependencies
  ✓ Simple setup
  ✓ Fast (<1ms)
  ✓ Built-in Python

Cons:
  ✗ Per-worker cache
  ✗ Lost on restart
  ✗ Doesn't scale
```

## Target Architecture (Redis)

```
┌─────────────────────┐    ┌─────────────────────┐
│  Railway Instance 1 │    │  Railway Instance 2 │
│                     │    │                     │
│  ┌──────────────┐  │    │  ┌──────────────┐  │
│  │  FastAPI App │──┼────┼──│  FastAPI App │  │
│  └──────────────┘  │    │  └──────────────┘  │
└──────────┬──────────┘    └──────────┬──────────┘
           │                          │
           └──────────┬───────────────┘
                      │
              ┌───────▼────────┐
              │  Redis Cache   │
              │  (Shared)      │
              └────────────────┘

Pros:
  ✓ Shared across instances
  ✓ Persists across restarts
  ✓ Scales horizontally
  ✓ TTL support built-in

Cons:
  ✗ Additional service
  ✗ Network latency (1-5ms)
  ✗ More complexity
```

## Step 1: Add Redis to Railway

```bash
# In Railway dashboard or CLI
railway redis add

# This creates a Redis instance and sets REDIS_URL environment variable
# Example: redis://default:password@redis.railway.internal:6379
```

## Step 2: Install Redis Client

```bash
# Add to requirements.txt
redis==5.0.1

# Install
pip install redis==5.0.1

# Or with uv
uv pip install redis==5.0.1
```

## Step 3: Update Configuration

**File: `app/core/config.py`**

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Redis Configuration
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL (use for multi-instance caching)"
    )
    REDIS_CACHE_ENABLED: bool = Field(
        default=False,
        description="Enable Redis cache (falls back to LRU if False)"
    )
```

**Environment Variable:**

```bash
# In Railway or .env
REDIS_URL=redis://default:password@redis.railway.internal:6379
REDIS_CACHE_ENABLED=true
```

## Step 4: Update GIS Service

**File: `app/services/gis_service.py`**

Replace the cache implementation with Redis:

```python
"""
GIS service with Redis caching for parcel data lookups.
"""
from typing import Optional, Dict, Any
import logging
import json
from datetime import timedelta

import redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisGISCache:
    """Redis-backed cache for GIS parcel data."""

    def __init__(self, redis_url: str, ttl_hours: int = 24):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
            ttl_hours: Cache time-to-live in hours
        """
        self.redis_client = redis.from_url(
            redis_url,
            decode_responses=True,  # Auto-decode strings
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        self.ttl = int(timedelta(hours=ttl_hours).total_seconds())
        self._hits = 0
        self._misses = 0

    def _make_key(self, apn: str) -> str:
        """Generate Redis key for parcel APN."""
        return f"gis:parcel:{apn}"

    def get(self, apn: str) -> Optional[Dict[str, Any]]:
        """
        Get cached parcel data.

        Args:
            apn: Assessor's Parcel Number

        Returns:
            Cached parcel data or None
        """
        try:
            key = self._make_key(apn)
            data = self.redis_client.get(key)

            if data:
                self._hits += 1
                logger.info(f"Redis cache hit for APN {apn}")
                return json.loads(data)
            else:
                self._misses += 1
                return None

        except redis.RedisError as e:
            logger.error(f"Redis get error for APN {apn}: {e}")
            return None

    def set(self, apn: str, data: Dict[str, Any]):
        """
        Cache parcel data in Redis.

        Args:
            apn: Assessor's Parcel Number
            data: Parcel data to cache
        """
        try:
            key = self._make_key(apn)
            value = json.dumps(data)

            # Set with TTL (SETEX = atomic set + expiration)
            self.redis_client.setex(key, self.ttl, value)
            logger.info(f"Cached parcel data in Redis for APN {apn}")

        except redis.RedisError as e:
            logger.error(f"Redis set error for APN {apn}: {e}")

    def clear(self):
        """Clear all GIS cache keys."""
        try:
            # Scan for all gis:parcel:* keys
            cursor = 0
            count = 0

            while True:
                cursor, keys = self.redis_client.scan(
                    cursor,
                    match="gis:parcel:*",
                    count=100
                )

                if keys:
                    count += len(keys)
                    self.redis_client.delete(*keys)

                if cursor == 0:
                    break

            logger.info(f"Cleared {count} parcels from Redis cache")

        except redis.RedisError as e:
            logger.error(f"Redis clear error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            # Count cached parcels
            cursor = 0
            count = 0

            while True:
                cursor, keys = self.redis_client.scan(
                    cursor,
                    match="gis:parcel:*",
                    count=1000
                )
                count += len(keys)

                if cursor == 0:
                    break

            # Get Redis info
            info = self.redis_client.info("stats")
            total_keys = info.get("db0", {}).get("keys", 0)

            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "cached_parcels": count,
                "total_redis_keys": total_keys,
                "ttl_hours": self.ttl / 3600,
                "cache_hits": self._hits,
                "cache_misses": self._misses,
                "hit_rate_pct": round(hit_rate, 2),
                "backend": "redis",
            }

        except redis.RedisError as e:
            logger.error(f"Redis stats error: {e}")
            return {
                "error": str(e),
                "backend": "redis",
            }


# Initialize cache based on configuration
if settings.REDIS_CACHE_ENABLED and settings.REDIS_URL:
    logger.info("Initializing Redis GIS cache")
    _gis_cache = RedisGISCache(
        redis_url=settings.REDIS_URL,
        ttl_hours=settings.GIS_CACHE_TTL_HOURS
    )
else:
    logger.info("Initializing in-memory LRU cache (Redis disabled)")
    # Fall back to LRU cache (existing implementation)
    from functools import lru_cache
    _gis_cache = GISCache(
        max_size=settings.GIS_CACHE_MAX_SIZE,
        ttl_hours=settings.GIS_CACHE_TTL_HOURS
    )


async def get_parcel_from_gis_cached(apn: str) -> Optional[Dict[str, Any]]:
    """
    Get parcel data from GIS with caching (Redis or LRU).

    Automatically uses Redis if REDIS_CACHE_ENABLED=true,
    otherwise falls back to in-memory LRU cache.

    Args:
        apn: Assessor's Parcel Number

    Returns:
        Parcel data dict or None if not found
    """
    # Check cache first
    cached = _gis_cache.get(apn)
    if cached:
        return cached

    # Cache miss - call GIS API
    try:
        logger.info(f"Cache miss for APN {apn} - calling GIS API")
        data = await query_parcel_by_apn(apn)

        if data:
            _gis_cache.set(apn, data)

        return data
    except Exception as e:
        logger.error(f"GIS API error for APN {apn}: {e}")
        return None


def clear_gis_cache():
    """Clear the GIS cache (Redis or LRU)."""
    _gis_cache.clear()
    logger.info("GIS cache cleared")


def get_cache_stats() -> Dict[str, Any]:
    """Get current cache statistics (Redis or LRU)."""
    return _gis_cache.get_stats()
```

## Step 5: Test Redis Connection

**Create: `scripts/test_redis.py`**

```python
"""Test Redis connection and cache operations."""
import redis
from app.core.config import settings

def test_redis():
    """Test Redis connection."""
    if not settings.REDIS_URL:
        print("❌ REDIS_URL not configured")
        return False

    try:
        # Connect to Redis
        client = redis.from_url(settings.REDIS_URL)

        # Test ping
        response = client.ping()
        print(f"✓ Redis PING: {response}")

        # Test set/get
        client.set("test_key", "test_value", ex=60)
        value = client.get("test_key")
        print(f"✓ Redis SET/GET: {value}")

        # Test delete
        client.delete("test_key")
        print("✓ Redis DELETE")

        # Get info
        info = client.info("server")
        print(f"✓ Redis version: {info.get('redis_version')}")

        print("\n✓ Redis connection successful!")
        return True

    except redis.RedisError as e:
        print(f"❌ Redis error: {e}")
        return False

if __name__ == "__main__":
    test_redis()
```

**Run test:**

```bash
./venv/bin/python scripts/test_redis.py
```

## Step 6: Deploy and Monitor

1. **Deploy to Railway:**
   ```bash
   git add .
   git commit -m "Upgrade to Redis cache for multi-instance deployment"
   git push railway main
   ```

2. **Monitor cache performance:**
   ```bash
   # Check cache stats
   curl https://your-api.railway.app/api/v1/admin/cache/stats

   # Expected response:
   {
     "cached_parcels": 150,
     "total_redis_keys": 150,
     "ttl_hours": 24,
     "cache_hits": 456,
     "cache_misses": 150,
     "hit_rate_pct": 75.25,
     "backend": "redis"
   }
   ```

3. **Monitor Redis metrics in Railway dashboard:**
   - Memory usage
   - Connected clients
   - Operations per second
   - Hit rate

## Performance Comparison

| Metric | LRU Cache | Redis Cache |
|--------|-----------|-------------|
| Cache hit latency | <1ms | 1-5ms |
| Shared across instances | ❌ No | ✓ Yes |
| Survives restarts | ❌ No | ✓ Yes |
| Horizontal scaling | ❌ No | ✓ Yes |
| Setup complexity | Simple | Moderate |
| Infrastructure cost | Free | ~$5-10/month |

## Rollback Plan

If Redis has issues, simply disable it:

```bash
# In Railway environment variables
REDIS_CACHE_ENABLED=false
```

The app will automatically fall back to LRU cache without code changes.

## Cost Estimate

Railway Redis pricing (as of 2025):

- **Hobby**: $5/month (500 MB)
- **Pro**: $10/month (2 GB)
- **Custom**: Contact for larger

For this use case (parcel caching):
- ~1000 parcels × 1KB each = 1 MB
- **Hobby tier is sufficient** ($5/month)

## Monitoring Checklist

After upgrading to Redis:

- [ ] Cache hit rate >50% (check `/admin/cache/stats`)
- [ ] Redis memory usage <50% of limit
- [ ] No connection errors in logs
- [ ] All instances sharing cache (check hit rate across deploys)
- [ ] Cache TTL working (parcels expire after 24h)
- [ ] Clear cache endpoint works (`POST /admin/cache/clear`)

## References

- [Redis Python Client Docs](https://redis.readthedocs.io/)
- [Railway Redis Docs](https://docs.railway.app/databases/redis)
- [FastAPI Caching Best Practices](https://fastapi.tiangolo.com/advanced/custom-response/)

## Support

For issues with Redis upgrade:

1. Check Railway logs for Redis connection errors
2. Verify `REDIS_URL` is set correctly
3. Test connection with `scripts/test_redis.py`
4. Fall back to LRU cache if needed: `REDIS_CACHE_ENABLED=false`
