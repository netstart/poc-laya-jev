import os
import json
import time
import hashlib
import re
import logging
from typing import Optional
from pathlib import Path
from collections import OrderedDict

logger = logging.getLogger(__name__)


class LRUCache:
    def __init__(self, max_items: int = 500, ttl_seconds: int = 1800):
        self.max_items = max_items
        self.ttl = ttl_seconds
        self._store: OrderedDict[str, tuple[dict, float]] = OrderedDict()

    def _normalize_key(self, text: str) -> str:
        t = text.lower()
        t = re.sub(r"[^\w\s]", "", t, flags=re.UNICODE)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _make_key(self, q: str, fresh: bool) -> str:
        base = self._normalize_key(q)
        return f"{base}|fresh={1 if fresh else 0}"

    def get(self, q: str, fresh: bool = False) -> Optional[dict]:
        if fresh:
            return None
        key = self._make_key(q, fresh)
        entry = self._store.get(key)
        if entry is None:
            return None
        data, ts = entry
        if time.time() - ts > self.ttl:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return data

    def put(self, q: str, fresh: bool, data: dict) -> None:
        if fresh:
            return
        key = self._make_key(q, fresh)
        self._store[key] = (data, time.time())
        if len(self._store) > self.max_items:
            self._store.popitem(last=False)

    def stats(self) -> dict:
        return {"items": len(self._store), "max": self.max_items, "ttl": self.ttl}


_cache: Optional[LRUCache] = None


def get_cache() -> LRUCache:
    global _cache
    if _cache is None:
        from app.config import settings
        _cache = LRUCache(max_items=settings.CACHE_MAX_ITEMS, ttl_seconds=settings.CACHE_TTL_SECONDS)
    return _cache
