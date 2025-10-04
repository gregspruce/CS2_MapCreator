"""
CS2 Cache Management Module

Implements LRU (Least Recently Used) caching for expensive operations.
This is the OPTIMAL caching strategy for this use case.

LRU Cache Explanation:
- Keeps N most recently used items in memory
- When cache is full, evicts least recently used item
- O(1) access time using hash map + doubly linked list
- Python's functools.lru_cache provides this built-in

Why LRU is optimal:
- Simple, proven algorithm (used everywhere)
- Optimal for temporal locality (recent = likely reused)
- Python built-in implementation is highly optimized
- Perfect for preset-based workflow

Alternative strategies rejected:
- LFU (Least Frequently Used): Complex, no benefit here
- FIFO: Doesn't account for usage patterns
- Random: Unpredictable performance
- MRU: Opposite of what we want

LRU is the clear winner.
"""

import functools
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Optional, Callable
import numpy as np


class CacheManager:
    """
    Manages caching for expensive operations.

    Two-tier caching strategy:
    1. Memory cache: Fast, limited size (using functools.lru_cache)
    2. Disk cache: Slower, larger capacity (using pickle files)

    Why two-tier:
    - Memory cache: Lightning fast for active work
    - Disk cache: Persist across sessions
    - Best of both worlds
    """

    def __init__(self,
                 cache_dir: Optional[Path] = None,
                 max_memory_items: int = 32,
                 max_disk_size_mb: int = 1024):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for disk cache (None = default)
            max_memory_items: Max items in memory cache
            max_disk_size_mb: Max disk cache size in megabytes

        Default cache directory:
        - ~/.cs2_heightmaps/cache/
        - Cross-platform compatible
        - User-specific (no permissions issues)
        """
        if cache_dir is None:
            home = Path.home()
            cache_dir = home / '.cs2_heightmaps' / 'cache'

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_memory_items = max_memory_items
        self.max_disk_size_mb = max_disk_size_mb

    def _make_key(self, *args, **kwargs) -> str:
        """
        Create cache key from function arguments.

        Uses JSON + SHA256 for stable, collision-resistant keys.

        Why this approach:
        - JSON: Human-readable, debuggable
        - SHA256: Collision-resistant hash
        - Stable: Same inputs = same key

        Note: Only works with JSON-serializable arguments.
        For NumPy arrays, use array_cache_key().
        """
        # Convert args and kwargs to JSON
        key_data = {
            'args': args,
            'kwargs': kwargs
        }

        json_str = json.dumps(key_data, sort_keys=True)

        # Hash to fixed-length key
        return hashlib.sha256(json_str.encode()).hexdigest()

    def array_cache_key(self, array: np.ndarray) -> str:
        """
        Create cache key for NumPy array.

        Uses array hash for fast, collision-resistant key.

        Why not use the array itself:
        - Arrays are large, slow to serialize
        - Hash is fast and sufficient for cache key
        - Collision risk is acceptably low

        Note: Different arrays with same values = same key
        This is desired behavior (content-based caching).
        """
        # Use NumPy's built-in array hash
        array_bytes = array.tobytes()
        return hashlib.sha256(array_bytes).hexdigest()

    def disk_cache_get(self, key: str) -> Optional[Any]:
        """
        Get item from disk cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found

        File format:
        - Pickle for Python objects
        - Compressed with highest protocol
        - Fast serialization/deserialization
        """
        cache_file = self.cache_dir / f"{key}.pkl"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception:
            # Corrupted cache file, ignore
            return None

    def disk_cache_set(self, key: str, value: Any) -> bool:
        """
        Store item in disk cache.

        Args:
            key: Cache key
            value: Value to cache

        Returns:
            True if stored successfully

        Size management:
        - Check total cache size
        - If over limit, delete oldest files
        - LRU eviction at disk level
        """
        # Check cache size before adding
        self._enforce_disk_cache_limit()

        cache_file = self.cache_dir / f"{key}.pkl"

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
            return True
        except Exception:
            return False

    def _enforce_disk_cache_limit(self) -> None:
        """
        Enforce disk cache size limit.

        Algorithm:
        1. Calculate total cache size
        2. If over limit, delete oldest files until under limit
        3. LRU at directory level (file modification time)

        Why file modification time:
        - Access time not reliable (varies by OS)
        - Modification time = last cache write
        - Simple, works everywhere
        """
        # Get all cache files with sizes
        cache_files = []
        total_size = 0

        for cache_file in self.cache_dir.glob('*.pkl'):
            try:
                size = cache_file.stat().st_size
                mtime = cache_file.stat().st_mtime
                cache_files.append((cache_file, size, mtime))
                total_size += size
            except Exception:
                continue

        # Convert to MB
        total_size_mb = total_size / (1024 * 1024)

        # If over limit, delete oldest files
        if total_size_mb > self.max_disk_size_mb:
            # Sort by modification time (oldest first)
            cache_files.sort(key=lambda x: x[2])

            # Delete until under limit
            for cache_file, size, mtime in cache_files:
                if total_size_mb <= self.max_disk_size_mb:
                    break

                try:
                    cache_file.unlink()
                    total_size_mb -= size / (1024 * 1024)
                except Exception:
                    continue

    def clear_disk_cache(self) -> int:
        """
        Clear all disk cache files.

        Returns:
            Number of files deleted

        Use cases:
        - Free up disk space
        - Force regeneration
        - Testing
        """
        count = 0

        for cache_file in self.cache_dir.glob('*.pkl'):
            try:
                cache_file.unlink()
                count += 1
            except Exception:
                continue

        return count

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats:
            - num_files: Number of cached files
            - total_size_mb: Total cache size
            - oldest_file: Oldest cache entry (timestamp)
            - newest_file: Newest cache entry (timestamp)

        Use case:
        - Monitor cache usage
        - Debug cache behavior
        - UI display
        """
        cache_files = list(self.cache_dir.glob('*.pkl'))
        num_files = len(cache_files)

        if num_files == 0:
            return {
                'num_files': 0,
                'total_size_mb': 0.0,
                'oldest_file': None,
                'newest_file': None
            }

        total_size = 0
        oldest_time = float('inf')
        newest_time = 0.0

        for cache_file in cache_files:
            try:
                size = cache_file.stat().st_size
                mtime = cache_file.stat().st_mtime

                total_size += size
                oldest_time = min(oldest_time, mtime)
                newest_time = max(newest_time, mtime)
            except Exception:
                continue

        return {
            'num_files': num_files,
            'total_size_mb': total_size / (1024 * 1024),
            'oldest_file': oldest_time,
            'newest_file': newest_time
        }


def cached_operation(cache_manager: CacheManager,
                    use_disk: bool = True):
    """
    Decorator for caching expensive operations.

    Args:
        cache_manager: CacheManager instance
        use_disk: Use disk cache in addition to memory cache

    Usage:
        @cached_operation(cache_manager)
        def expensive_function(arg1, arg2):
            # ... expensive computation ...
            return result

    How it works:
    1. Check memory cache (fast)
    2. If miss, check disk cache (slower)
    3. If miss, compute and cache result
    4. Return cached or computed result

    Memory cache:
    - Uses functools.lru_cache (Python built-in)
    - O(1) access time
    - Limited size (evicts LRU)

    Disk cache:
    - Uses pickle files
    - Persists across sessions
    - Larger capacity
    """
    def decorator(func: Callable) -> Callable:
        # Wrap with memory cache
        cached_func = functools.lru_cache(maxsize=cache_manager.max_memory_items)(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try disk cache if enabled
            if use_disk:
                cache_key = cache_manager._make_key(*args, **kwargs)
                disk_result = cache_manager.disk_cache_get(cache_key)

                if disk_result is not None:
                    return disk_result

            # Compute (memory cache handles this)
            result = cached_func(*args, **kwargs)

            # Save to disk cache
            if use_disk:
                cache_manager.disk_cache_set(cache_key, result)

            return result

        # Expose cache_clear for testing
        wrapper.cache_clear = cached_func.cache_clear

        return wrapper

    return decorator
