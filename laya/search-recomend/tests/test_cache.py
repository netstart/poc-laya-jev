import pytest
import time
from app.cache import LRUCache, get_cache


def test_normalize_key():
    cache = LRUCache(max_items=10, ttl_seconds=60)
    assert cache._normalize_key("Presente Pra Mae") == "presente pra mae"
    assert cache._normalize_key("  a   b  c  ") == "a b c"
    assert cache._normalize_key(" Cafe! ") == "cafe"


def test_make_key_fresh_flag():
    cache = LRUCache(max_items=10, ttl_seconds=60)
    assert cache._make_key("query", False) == "query|fresh=0"
    assert cache._make_key("query", True) == "query|fresh=1"


def test_get_cache_miss():
    cache = LRUCache(max_items=10, ttl_seconds=60)
    assert cache.get("inexistente") is None
    assert cache.get("inexistente", fresh=True) is None


def test_put_and_get_cache_hit():
    cache = LRUCache(max_items=10, ttl_seconds=60)
    cache.put("query", False, {"ok": True})
    assert cache.get("query") == {"ok": True}
    assert cache.get("query", fresh=True) is None


def test_cache_ttl_expiry():
    cache = LRUCache(max_items=10, ttl_seconds=0)
    cache.put("query", False, {"ok": True})
    time.sleep(0.05)
    assert cache.get("query") is None


def test_cache_lru_eviction():
    cache = LRUCache(max_items=2, ttl_seconds=60)
    cache.put("a", False, {"id": 1})
    cache.put("b", False, {"id": 2})
    cache.put("c", False, {"id": 3})
    assert cache.get("a") is None
    assert cache.get("b") == {"id": 2}
    assert cache.get("c") == {"id": 3}


def test_cache_stats():
    cache = LRUCache(max_items=10, ttl_seconds=60)
    cache.put("a", False, {})
    cache.put("b", False, {})
    stats = cache.stats()
    assert stats["items"] == 2
    assert stats["max"] == 10
    assert stats["ttl"] == 60


def test_get_cache_singleton():
    from app.cache import _cache
    _cache_instance = None
    import app.cache as cache_module
    cache_module._cache = None
    c1 = get_cache()
    c2 = get_cache()
    assert c1 is c2
    cache_module._cache = _cache_instance
