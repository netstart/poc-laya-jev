import pytest
from app.search_engine import tokenize, keyword_search, SearchEngine
from app.schemas import Producto


def test_tokenize():
    text = "Presente para minha mae, jardim!"
    tokens = tokenize(text)
    assert "presente" in tokens
    assert "jardim" in tokens
    assert "para" not in tokens
    assert "minha" in tokens
    assert "," not in tokens


def test_tokenize_empty():
    assert tokenize("") == []
    assert tokenize("!!!") == []


def test_keyword_search_no_match():
    productos = [
        Producto(id="p1", nombre="X", precio=10, categoria="casa", publico="familia", departamento="casa", descripcion="", tags=[])
    ]
    result = keyword_search("nao existe", productos)
    assert result == []


def test_keyword_search_match():
    productos = [
        Producto(id="p1", nombre="Kit Jardinagem", precio=10, categoria="jardim", publico="mae", departamento="jardim", descripcion="para jardinagem", tags=["jardim"]),
        Producto(id="p2", nombre="Carregador", precio=10, categoria="eletronicos", publico="familia", departamento="eletronicos", descripcion="", tags=[]),
    ]
    result = keyword_search("jardinagem", productos)
    assert len(result) == 1
    assert result[0].id == "p1"


def test_keyword_search_tie_break_by_price():
    productos = [
        Producto(id="p1", nombre="A", precio=100, categoria="casa", publico="familia", departamento="casa", descripcion="casa", tags=[]),
        Producto(id="p2", nombre="B", precio=50, categoria="casa", publico="familia", departamento="casa", descripcion="casa", tags=[]),
    ]
    result = keyword_search("casa", productos)
    assert result[0].id == "p2"
    assert result[1].id == "p1"


def test_search_engine_cache_hit(monkeypatch):
    from app.cache import LRUCache
    monkeypatch.setattr("app.search_engine.get_cache", lambda: LRUCache(max_items=10, ttl_seconds=60))
    engine = SearchEngine.__new__(SearchEngine)
    engine.productos = []
    engine.laya = None
    engine.cache = LRUCache(max_items=10, ttl_seconds=60)
    engine.cache.put("query", False, {"ok": True, "cached": False})
    result = engine.buscar("query", fresh=False)
    assert result["cached"] is True
    assert result["ok"] is True
