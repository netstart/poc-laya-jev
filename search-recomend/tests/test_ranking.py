import pytest
from app.ranking import rank_productos, count_good_options, top_n, over_budget_suggestions
from app.schemas import Producto, ScoreProducto


def make_producto(id, precio):
    return Producto(id=id, nombre=f"Produto {id}", precio=precio, categoria="casa", publico="familia", departamento="casa", descripcion="", tags=[])


def make_scores(ids_scores):
    return {id: ScoreProducto(producto_id=id, score=score, probabilities={"0":0,"1":0,"2":0,"3":1}, confidence=0.9) for id, score in ids_scores}


def test_rank_within_budget_first():
    ps = [make_producto("p1", 100), make_producto("p2", 200), make_producto("p3", 50)]
    scores = make_scores([("p1", 2.0), ("p2", 3.0), ("p3", 1.0)])
    ranked = rank_productos(ps, scores, orcamento_max=150)
    assert ranked[0].id == "p1"
    assert ranked[1].id == "p3"
    assert ranked[2].id == "p2"


def test_rank_tie_break_lower_price():
    ps = [make_producto("p1", 100), make_producto("p2", 80)]
    scores = make_scores([("p1", 2.0), ("p2", 2.0)])
    ranked = rank_productos(ps, scores, orcamento_max=200)
    assert ranked[0].id == "p2"
    assert ranked[1].id == "p1"


def test_count_good_options():
    scores = make_scores([("p1", 2.0), ("p2", 1.5), ("p3", 2.5)])
    assert count_good_options(scores, threshold=2.0) == 2


def test_top_n():
    ps = [make_producto(f"p{i}", i * 10) for i in range(1, 6)]
    scores = make_scores([("p1", 2.0), ("p2", 1.0), ("p3", 3.0), ("p4", 1.5), ("p5", 0.5)])
    top = top_n(ps, scores, n=3, min_score=1.0)
    assert len(top) == 3
    assert top[0].id == "p3"


def test_over_budget_suggestions():
    ps = [make_producto("p1", 100), make_producto("p2", 200), make_producto("p3", 300)]
    scores = make_scores([("p1", 2.0), ("p2", 2.0), ("p3", 1.8)])
    over = over_budget_suggestions(ps, scores, orcamento_max=150, max_items=3, min_score=1.5)
    assert len(over) == 2
    assert over[0].id == "p2"


def test_over_budget_suggestions_none():
    ps = [make_producto("p1", 100), make_producto("p2", 200)]
    scores = make_scores([("p1", 2.0), ("p2", 2.0)])
    over = over_budget_suggestions(ps, scores, orcamento_max=None)
    assert over == []
