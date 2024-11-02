import asyncio
import json
import time
from collections import OrderedDict
from typing import Any, Optional, Tuple


class CacheEntry:
    __slots__ = ("data", "timestamp", "size")

    def __init__(self, data: Any, timestamp: float, size: int):
        self.data = data
        self.timestamp = timestamp
        self.size = size


class Cache:
    """
    A simple LRU cache with TTL and size limit.

    Attributes
    ----------
    ttl: int
        Time to live for cache entries, in seconds.
    maxbytes: int
        Maximum total size of cached data in bytes.
    """

    def __init__(self, ttl: int, maxbytes: int = 250 * 1024 * 1024):  # 250 MiB
        self.ttl = ttl
        self.maxbytes = maxbytes
        self.cache: OrderedDict[Tuple, CacheEntry] = OrderedDict()
        self.total_size = 0
        self.lock = asyncio.Lock()

    async def get(self, key: Tuple) -> Optional[Any]:
        async with self.lock:
            entry = self.cache.get(key)
            if entry:
                if time.time() - entry.timestamp < self.ttl:
                    self.cache.move_to_end(key)
                    return entry.data
                else:
                    self._remove_entry(key)
            return None

    async def set(self, key: Tuple, data: Any):
        async with self.lock:
            size = len(json.dumps(data).encode("utf-8"))
            entry = CacheEntry(data, time.time(), size)
            self.cache[key] = entry
            self.cache.move_to_end(key)
            self.total_size += size
            await self._enforce_size_limit()

    def _remove_entry(self, key: Tuple):
        entry = self.cache.pop(key, None)
        if entry:
            self.total_size -= entry.size

    async def _enforce_size_limit(self):
        while self.total_size > self.maxbytes:
            key, entry = self.cache.popitem(last=False)
            self.total_size -= entry.size
            await asyncio.sleep(0)
