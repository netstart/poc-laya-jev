from typing import List, Dict, Optional
from app.schemas import Producto, ScoreProducto


def rank_productos(
    productos: List[Producto],
    scores: Dict[str, ScoreProducto],
    orcamento_max: Optional[float] = None,
) -> List[Producto]:
    dentro = []
    fora = []
    for p in productos:
        s = scores.get(p.id)
        score_val = s.score if s else 0.0
        if orcamento_max is not None and p.precio > orcamento_max:
            fora.append((p, score_val))
        else:
            dentro.append((p, score_val))
    dentro.sort(key=lambda x: (-x[1], x[0].precio))
    fora.sort(key=lambda x: (-x[1], x[0].precio))
    return [p for p, _ in dentro + fora]


def count_good_options(scores: Dict[str, ScoreProducto], threshold: float = 2.0) -> int:
    return sum(1 for s in scores.values() if s.score >= threshold)


def top_n(productos: List[Producto], scores: Dict[str, ScoreProducto], n: int = 8, min_score: float = 1.0) -> List[Producto]:
    ranked = rank_productos(productos, scores)
    return [p for p in ranked if scores.get(p.id, ScoreProducto(producto_id=p.id, score=0, probabilities={}, confidence=0)).score >= min_score][:n]


def over_budget_suggestions(productos: List[Producto], scores: Dict[str, ScoreProducto], orcamento_max: Optional[float], max_items: int = 3, min_score: float = 1.5) -> List[Producto]:
    if orcamento_max is None:
        return []
    filtered = [p for p in productos if p.precio > orcamento_max and scores.get(p.id, ScoreProducto(producto_id=p.id, score=0, probabilities={}, confidence=0)).score >= min_score]
    filtered.sort(key=lambda p: (-scores[p.id].score, p.precio))
    return filtered[:max_items]
