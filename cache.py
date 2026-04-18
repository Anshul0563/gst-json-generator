"""
cache.py - Caching System for Performance Optimization
In-memory cache with TTL and size management
"""

import time
from typing import Any, Dict, Optional, Tuple


class CacheEntry:
    """Individual cache entry with TTL."""
    
    def __init__(self, value: Any, ttl: int = 3600):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.created_at > self.ttl
    
    def get_size_mb(self) -> float:
        """Estimate size in MB."""
        import sys
        return sys.getsizeof(self.value) / (1024 * 1024)


class Cache:
    """Advanced caching system with TTL and size management."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._cache: Dict[str, CacheEntry] = {}
            self._initialized = True
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            return None
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache with TTL."""
        from config import get_config
        config = get_config()
        
        if not config.get('cache.enabled', True):
            return
        
        # Check size limit
        max_size_mb = config.get('cache.max_size_mb', 100)
        total_size = sum(e.get_size_mb() for e in self._cache.values())
        
        if total_size > max_size_mb:
            self._evict_oldest()
        
        self._cache[key] = CacheEntry(value, ttl)
    
    def delete(self, key: str) -> None:
        """Delete entry from cache."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)
    
    def _evict_oldest(self) -> None:
        """Evict oldest entry when cache is full."""
        if not self._cache:
            return
        
        oldest_key = min(self._cache.keys(), 
                        key=lambda k: self._cache[k].created_at)
        del self._cache[oldest_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        self.cleanup_expired()
        total_size = sum(e.get_size_mb() for e in self._cache.values())
        return {
            'entries': len(self._cache),
            'total_size_mb': round(total_size, 2),
            'expired_count': sum(1 for e in self._cache.values() if e.is_expired())
        }


def get_cache() -> Cache:
    """Get or create cache instance."""
    return Cache()


# Decorator for caching function results
def cached(ttl: int = 3600, key_prefix: str = ''):
    """Decorator to cache function results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Build cache key
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{sorted(kwargs.items())}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator
