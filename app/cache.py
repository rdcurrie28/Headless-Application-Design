import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

T = TypeVar("T")


class TTLCache:
    def __init__(self, ttl_seconds: int, max_entries: int = 5000) -> None:
        self._ttl = ttl_seconds
        self._max = max_entries
        self._data: dict[str, tuple[float, Any]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _fresh(self, key: str) -> tuple[bool, Any]:
        hit = self._data.get(key)
        if hit and hit[0] > time.monotonic():
            return True, hit[1]
        return False, None

    def _store(self, key: str, value: Any) -> None:
        if len(self._data) >= self._max:
            self._data.pop(next(iter(self._data)))
        self._data[key] = (time.monotonic() + self._ttl, value)

    async def get_or_load(self, key: str, loader: Callable[[], Awaitable[T]]) -> T:
        if self._ttl <= 0:
            return await loader()
        ok, value = self._fresh(key)
        if ok:
            return value
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            ok, value = self._fresh(key)
            if ok:
                return value
            value = await loader()
            self._store(key, value)
            return value

    def invalidate(self, prefix: str = "") -> None:
        for key in [k for k in self._data if k.startswith(prefix)]:
            self._data.pop(key, None)
