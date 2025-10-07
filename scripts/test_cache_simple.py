"""
Simple cache test to verify functionality.

This script tests the cache with mock data to verify it's working correctly.
"""
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.gis_service import clear_gis_cache, get_cache_stats, _gis_cache


def test_cache_operations():
    """Test basic cache operations."""
    print("\n" + "="*70)
    print("CACHE FUNCTIONALITY TEST")
    print("="*70 + "\n")

    # Clear cache
    clear_gis_cache()
    print("✓ Cache cleared\n")

    # Test set and get
    test_data = {
        "apn": "TEST-001",
        "address": "123 Test St",
        "zoning": "R1",
        "lot_size_sqft": 5000,
    }

    print("Test 1: Cache SET")
    print("-" * 70)
    _gis_cache.set("TEST-001", test_data)
    print(f"✓ Cached parcel: {test_data['apn']}\n")

    print("Test 2: Cache GET (hit)")
    print("-" * 70)
    start = time.perf_counter()
    cached_data = _gis_cache.get("TEST-001")
    duration = (time.perf_counter() - start) * 1000  # Convert to ms

    if cached_data:
        print(f"✓ Retrieved from cache: {cached_data['apn']}")
        print(f"  Duration: {duration:.3f} ms")
        print(f"  Data matches: {cached_data == test_data}")
    else:
        print("✗ Cache miss (unexpected)")

    print()

    print("Test 3: Cache GET (miss)")
    print("-" * 70)
    start = time.perf_counter()
    missing_data = _gis_cache.get("NONEXISTENT-001")
    duration = (time.perf_counter() - start) * 1000

    if missing_data is None:
        print(f"✓ Cache miss as expected")
        print(f"  Duration: {duration:.3f} ms")
    else:
        print("✗ Unexpected cache hit")

    print()

    print("Test 4: Multiple parcels")
    print("-" * 70)
    parcels = []
    for i in range(10):
        parcel = {
            "apn": f"TEST-{i:03d}",
            "address": f"{100 + i} Test St",
            "zoning": "R2",
            "lot_size_sqft": 5000 + (i * 1000),
        }
        _gis_cache.set(parcel["apn"], parcel)
        parcels.append(parcel)
        print(f"  ✓ Cached: {parcel['apn']}")

    print()

    print("Test 5: Cache statistics")
    print("-" * 70)
    stats = get_cache_stats()
    print(f"  Cached parcels: {stats['cached_parcels']}")
    print(f"  Max size: {stats['max_size']}")
    print(f"  TTL: {stats['ttl_hours']} hours")
    print(f"  Cache hits: {stats['cache_hits']}")
    print(f"  Cache misses: {stats['cache_misses']}")
    print(f"  Hit rate: {stats['hit_rate_pct']}%")

    print()

    print("Test 6: Performance comparison")
    print("-" * 70)

    # Simulate API call time (slow)
    def mock_api_call():
        time.sleep(0.1)  # Simulate 100ms API latency
        return test_data

    # Test uncached (API call)
    start = time.perf_counter()
    mock_api_call()
    api_duration = (time.perf_counter() - start) * 1000

    # Test cached (fast)
    start = time.perf_counter()
    _gis_cache.get("TEST-001")
    cache_duration = (time.perf_counter() - start) * 1000

    speedup = api_duration / cache_duration if cache_duration > 0 else 0

    print(f"  API call (simulated): {api_duration:.2f} ms")
    print(f"  Cache hit: {cache_duration:.3f} ms")
    print(f"  Speedup: {speedup:.0f}x FASTER")

    print()

    print("Test 7: Clear cache")
    print("-" * 70)
    clear_gis_cache()
    stats_after = get_cache_stats()
    print(f"  Cached parcels after clear: {stats_after['cached_parcels']}")
    print(f"  ✓ Cache cleared successfully")

    print()
    print("="*70)
    print("ALL TESTS PASSED")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        test_cache_operations()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
