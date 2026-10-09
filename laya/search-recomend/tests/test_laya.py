import pytest
from app.laya_engine import LayaEngine
from app.schemas import Producto

laya = pytest.importorskip("laya")


def make_producto(id, nombre, categoria="casa", publico="familia"):
    return Producto(id=id, nombre=nombre, precio=100.0, categoria=categoria, publico=publico, departamento=categoria, descripcion="", tags=[])


def test_laya_understand_query_basic():
    engine = LayaEngine(checkpoint="convaiinnovations/laya-multilingual", device="cpu")
    res = engine.understand_query("presente pra minha mãe que ama jardinagem até 150 reais")
    assert res.intencion == "presente"
    assert res.categoria == "jardim"
    assert res.destinatario == "mae"
    assert res.orcamento_max == 150


def test_laya_understand_query_portuguese_dog():
    engine = LayaEngine(checkpoint="convaiinnovations/laya-multilingual", device="cpu")
    res = engine.understand_query("meu cachorro destrói todos os brinquedos")
    assert res.intencion == "uso_proprio"
    assert res.categoria == "pet"
    assert res.destinatario == "pet"
    assert res.confianca > 0


def test_laya_understand_query_english_gift():
    engine = LayaEngine(checkpoint="convaiinnovations/laya-multilingual", device="cpu")
    res = engine.understand_query("gift for a coffee lover")
    assert res.intencion == "presente"
    assert res.categoria == "cozinha"
    assert res.confianca > 0


def test_laya_score_products_returns_scores():
    engine = LayaEngine(checkpoint="convaiinnovations/laya-multilingual", device="cpu")
    productos = [make_producto("p1", "Vaso de plantas"), make_producto("p2", "Carregador celular")]
    scores = engine.score_products("jardim presente", productos)
    assert len(scores) == 2
    assert all(s.producto_id in ("p1", "p2") for s in scores)
    assert all(0 <= s.score <= 3 for s in scores)


def test_laya_score_products_dog_toy():
    engine = LayaEngine(checkpoint="convaiinnovations/laya-multilingual", device="cpu")
    productos = [
        make_producto("p1", "Brinquedo para Cachorro Resistente", categoria="pet", publico="pet"),
        make_producto("p2", "Racao Premium para Caes", categoria="pet", publico="pet"),
    ]
    scores = engine.score_products("meu cachorro destroi todos os brinquedos", productos)
    assert len(scores) == 2
    p1_score = next(s for s in scores if s.producto_id == "p1")
    assert p1_score.score >= 1.0


def test_laya_score_products_coffee_gift():
    engine = LayaEngine(checkpoint="convaiinnovations/laya-multilingual", device="cpu")
    productos = [
        make_producto("p1", "Cafeteira French Press", categoria="cozinha", publico="familia"),
        make_producto("p2", "Kit Canecas Ceramica", categoria="cozinha", publico="familia"),
    ]
    scores = engine.score_products("gift for a coffee lover", productos)
    assert len(scores) == 2
    top = max(scores, key=lambda s: s.score)
    assert top.score >= 1.0


def test_laya_real_understand_query_returns_valid_model():
    engine = LayaEngine(checkpoint="convaiinnovations/laya-multilingual", device="cpu")
    res = engine._understand_query_real("presente para minha mae que ama jardinagem")
    assert res.intencion in {"presente", "uso_proprio", "reposicao", "pesquisa"}
    assert res.confianca > 0
    assert isinstance(res.bruto, dict)


def test_laya_real_score_products_batch_shape():
    engine = LayaEngine(checkpoint="convaiinnovations/laya-multilingual", device="cpu")
    productos = [make_producto("p1", "Vaso de plantas"), make_producto("p2", "Carregador celular")]
    scores = engine._score_products_real("jardim presente", productos)
    assert len(scores) == 2
    for s in scores:
        assert 0 <= s.score <= 3
        assert 0 <= s.confidence <= 1
        assert isinstance(s.probabilities, dict)


def test_laya_fallback_without_model(monkeypatch):
    engine = LayaEngine(checkpoint="convaiinnovations/laya-multilingual", device="cpu")
    monkeypatch.setattr(engine, "_model", None)
    productos = [make_producto("p1", "Vaso de plantas")]
    scores = engine.score_products("query", productos)
    assert len(scores) == 1
    assert 0 <= scores[0].score <= 3

