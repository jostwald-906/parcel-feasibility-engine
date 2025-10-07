/**
 * GIS Query Cache
 *
 * LRU (Least Recently Used) cache for ArcGIS REST API responses.
 * Reduces redundant network requests when exploring the map.
 */

interface CacheEntry<T> {
  value: T;
  timestamp: number;
  hits: number;
}

interface CacheStats {
  size: number;
  maxSize: number;
  hits: number;
  misses: number;
  hitRate: number;
  oldestEntry: number;
  newestEntry: number;
}

export class LRUCache<T = any> {
  private cache: Map<string, CacheEntry<T>>;
  private maxSize: number;
  private ttl: number; // time to live in milliseconds
  private hits: number = 0;
  private misses: number = 0;

  constructor(maxSize: number = 100, ttlMinutes: number = 30) {
    this.cache = new Map();
    this.maxSize = maxSize;
    this.ttl = ttlMinutes * 60 * 1000;
  }

  /**
   * Generate cache key from service URL and query parameters
   */
  static generateKey(url: string, params?: Record<string, any>): string {
    if (!params) return url;

    // Sort params for consistent keys
    const sortedParams = Object.keys(params)
      .sort()
      .map((key) => `${key}=${JSON.stringify(params[key])}`)
      .join('&');

    return `${url}?${sortedParams}`;
  }

  /**
   * Get value from cache
   */
  get(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      this.misses++;
      return null;
    }

    // Check if expired
    if (Date.now() - entry.timestamp > this.ttl) {
      this.cache.delete(key);
      this.misses++;
      return null;
    }

    // Update hit count and move to end (most recent)
    entry.hits++;
    this.hits++;
    this.cache.delete(key);
    this.cache.set(key, entry);

    return entry.value;
  }

  /**
   * Set value in cache
   */
  set(key: string, value: T): void {
    // If at capacity, remove least recently used (first item)
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      if (firstKey) {
        this.cache.delete(firstKey);
      }
    }

    this.cache.set(key, {
      value,
      timestamp: Date.now(),
      hits: 0,
    });
  }

  /**
   * Check if key exists and is not expired
   */
  has(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;

    if (Date.now() - entry.timestamp > this.ttl) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Clear all cached entries
   */
  clear(): void {
    this.cache.clear();
    this.hits = 0;
    this.misses = 0;
  }

  /**
   * Clear expired entries
   */
  clearExpired(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > this.ttl) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Get cache statistics
   */
  getStats(): CacheStats {
    const entries = Array.from(this.cache.values());
    const timestamps = entries.map((e) => e.timestamp);

    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      hits: this.hits,
      misses: this.misses,
      hitRate: this.hits + this.misses > 0 ? this.hits / (this.hits + this.misses) : 0,
      oldestEntry: timestamps.length > 0 ? Math.min(...timestamps) : 0,
      newestEntry: timestamps.length > 0 ? Math.max(...timestamps) : 0,
    };
  }

  /**
   * Get all cache keys
   */
  keys(): string[] {
    return Array.from(this.cache.keys());
  }

  /**
   * Get cache size
   */
  size(): number {
    return this.cache.size;
  }

  /**
   * Remove specific key
   */
  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  /**
   * Get most frequently accessed entries
   */
  getTopEntries(count: number = 10): Array<{ key: string; hits: number; age: number }> {
    return Array.from(this.cache.entries())
      .map(([key, entry]) => ({
        key,
        hits: entry.hits,
        age: Date.now() - entry.timestamp,
      }))
      .sort((a, b) => b.hits - a.hits)
      .slice(0, count);
  }
}

/**
 * Global cache instance for GIS queries
 */
export const gisCache = new LRUCache(200, 30); // 200 entries, 30 min TTL

/**
 * Cache-enabled fetch function for ArcGIS REST API
 */
export async function cachedFetch<T = any>(
  url: string,
  params?: Record<string, any>
): Promise<T> {
  const cacheKey = LRUCache.generateKey(url, params);

  // Try to get from cache
  const cached = gisCache.get(cacheKey);
  if (cached !== null) {
    console.log(`[Cache HIT] ${url.split('/').pop()}`);
    return cached as T;
  }

  // Fetch from API
  const urlParts = url.split('/');
  console.log(`[Cache MISS] ${urlParts[urlParts.length - 1] || 'root'}`);

  const queryString = params
    ? '?' +
      Object.keys(params)
        .map((key) => `${key}=${encodeURIComponent(String(params[key]))}`)
        .join('&')
    : '';

  const response = await fetch(`${url}${queryString}`);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const data = await response.json();

  // Store in cache
  gisCache.set(cacheKey, data);

  return data as T;
}

/**
 * Prefetch and cache common queries
 */
export async function prefetchCommonData(): Promise<void> {
  console.log('Prefetching common GIS data...');

  // This would be called on app initialization to warm the cache
  // with frequently accessed data like zoning boundaries, transit stops, etc.

  // Example:
  // await cachedFetch('https://gis.santamonica.gov/.../Zoning/...', { where: '1=1', outFields: '*' });
}

/**
 * Cache invalidation by pattern
 */
export function invalidateByPattern(pattern: string | RegExp): number {
  const keys = gisCache.keys();
  let invalidated = 0;

  const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern;

  for (const key of keys) {
    if (regex.test(key)) {
      gisCache.delete(key);
      invalidated++;
    }
  }

  console.log(`Invalidated ${invalidated} cache entries matching pattern: ${pattern}`);
  return invalidated;
}

/**
 * Cache middleware for ArcGIS query functions
 */
export function withCache<TArgs extends any[], TResult>(
  fn: (...args: TArgs) => Promise<TResult>,
  keyGenerator: (...args: TArgs) => string
) {
  return async (...args: TArgs): Promise<TResult> => {
    const cacheKey = keyGenerator(...args);

    const cached = gisCache.get(cacheKey);
    if (cached !== null) {
      return cached as TResult;
    }

    const result = await fn(...args);
    gisCache.set(cacheKey, result);

    return result;
  };
}

/**
 * Auto-cleanup expired entries every 5 minutes
 */
if (typeof window !== 'undefined') {
  setInterval(() => {
    gisCache.clearExpired();
    const stats = gisCache.getStats();
    console.log('[GIS Cache] Cleanup completed', {
      size: stats.size,
      hitRate: (stats.hitRate * 100).toFixed(1) + '%',
    });
  }, 5 * 60 * 1000);
}

/**
 * Export cache statistics for monitoring
 */
export function getCacheStats(): CacheStats {
  return gisCache.getStats();
}

/**
 * Log cache performance to console
 */
export function logCacheStats(): void {
  const stats = gisCache.getStats();
  console.log('=== GIS Cache Statistics ===');
  console.log(`Size: ${stats.size}/${stats.maxSize}`);
  console.log(`Hits: ${stats.hits}`);
  console.log(`Misses: ${stats.misses}`);
  console.log(`Hit Rate: ${(stats.hitRate * 100).toFixed(1)}%`);
  console.log(`Age: ${((Date.now() - stats.oldestEntry) / 1000 / 60).toFixed(1)} min`);
  console.log('\nTop Entries:');
  console.table(gisCache.getTopEntries(5));
}
