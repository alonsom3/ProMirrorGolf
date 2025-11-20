"""
Cache manager for frequently accessed data.

This module provides an LRU (Least Recently Used) cache implementation
with TTL (Time-To-Live) support. It's used to cache:
- Session data (10 minute TTL)
- Shot data (5 minute TTL)
- Thumbnail images (1 hour TTL)
- Statistics (1 minute TTL)

The cache automatically evicts expired items and least-recently-used items
when the cache size limit is reached.

Usage:
    from core.cache_manager import get_session_cache, CacheManager
    
    # Use global cache instances
    cache = get_session_cache()
    value = cache.get("session_123")
    if value is None:
        value = load_session_from_db(123)
        cache.set("session_123", value)
    
    # Create custom cache
    custom_cache = CacheManager(max_size=100, default_ttl=300)
    cached_value = custom_cache.get_or_compute("key", expensive_function)
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Any, Callable

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Simple LRU cache with TTL (time-to-live) support.
    
    Uses OrderedDict for O(1) get/set operations and automatic LRU eviction.
    Expired items are removed on access. When cache is full, oldest items
    are evicted first.
    """
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        """
        Initialize cache manager.
        
        Args:
            max_size: Maximum number of items in cache
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self.cache:
            return None
        
        value, expiry_time = self.cache[key]
        
        if time.time() > expiry_time:
            # Expired - remove from cache
            del self.cache[key]
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl
        expiry_time = time.time() + ttl
        
        if key in self.cache:
            # Update existing
            self.cache[key] = (value, expiry_time)
            self.cache.move_to_end(key)
        else:
            # Add new
            if len(self.cache) >= self.max_size:
                # Remove oldest (first item)
                self.cache.popitem(last=False)
            
            self.cache[key] = (value, expiry_time)
    
    def invalidate(self, key: str) -> None:
        """Remove key from cache."""
        self.cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached items."""
        self.cache.clear()
    
    def get_or_compute(
        self,
        key: str,
        compute_func: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or compute if not found.
        
        Args:
            key: Cache key
            compute_func: Function to compute value if not cached
            ttl: Time-to-live in seconds
        
        Returns:
            Cached or computed value
        """
        value = self.get(key)
        if value is not None:
            return value
        
        value = compute_func()
        self.set(key, value, ttl)
        return value


# Global cache instances for different data types
_session_cache = CacheManager(max_size=50, default_ttl=600)  # 10 minutes
_shot_cache = CacheManager(max_size=500, default_ttl=300)  # 5 minutes
_thumbnail_cache = CacheManager(max_size=200, default_ttl=3600)  # 1 hour
_stats_cache = CacheManager(max_size=20, default_ttl=60)  # 1 minute


def get_session_cache() -> CacheManager:
    """Get session cache instance."""
    return _session_cache


def get_shot_cache() -> CacheManager:
    """Get shot cache instance."""
    return _shot_cache


def get_thumbnail_cache() -> CacheManager:
    """Get thumbnail cache instance."""
    return _thumbnail_cache


def get_stats_cache() -> CacheManager:
    """Get statistics cache instance."""
    return _stats_cache


def clear_all_caches() -> None:
    """Clear all caches."""
    _session_cache.clear()
    _shot_cache.clear()
    _thumbnail_cache.clear()
    _stats_cache.clear()

