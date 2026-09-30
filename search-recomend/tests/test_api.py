from fastapi.testclient import TestClient
from app.main import app
import app.main as main_module
from app.schemas import Producto
from app.laya_engine import LayaEngine
from app.search_engine import SearchEngine
import json
import pytest

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_app():
    if main_module._productos is None or len(main_module._productos) == 0:
        with open("data/catalogo.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        main_module._productos = [Producto(**p) for p in data]
        main_module._search = SearchEngine(main_module._productos, LayaEngine(checkpoint="laya-multilingual", device="cpu"))


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["engine"] == "laya"


def test_catalogo():
    r = client.get("/api/catalogo")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 120


def test_exemplos():
    r = client.get("/api/exemplos")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 8


def test_stats():
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert "cache" in data
    assert "productos" in data
    assert data["productos"] == 120


def test_buscar_validation():
    r = client.post("/api/buscar", json={"q": "a", "fresh": False})
    assert r.status_code == 400


def test_buscar_long():
    r = client.post("/api/buscar", json={"q": "a" * 301, "fresh": False})
    assert r.status_code in (400, 422)


def test_buscar_ok():
    r = client.post("/api/buscar", json={"q": "presente pra mae jardim", "fresh": True})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["n_produtos"] == 120
    assert "entendimiento" in data
    assert "scores" in data
    assert "ordem" in data
