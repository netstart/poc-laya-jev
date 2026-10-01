from typing import List, Dict, Optional
from app.schemas import Producto, ScoreProducto


def rank_productos(
    productos: List[Producto],
    scores: Dict[str, ScoreProducto],
    orcamento_max: Optional[float] = None,
) -> List[Producto]:
    """
    Ranqueia produtos separando em dois grupos: dentro do orçamento e fora do orçamento.
    Ambos os grupos são ordenados por score decrescente e depois por preço crescente.
    Retorna lista concatenada: primeiro os dentro do orçamento, depois os fora.
    """
    dentro = []  # produtos dentro do orçamento (ou sem orçamento definido)
    fora = []    # produtos que excedem o orçamento
    for p in productos:
        s = scores.get(p.id)
        score_val = s.score if s else 0.0
        if orcamento_max is not None and p.precio > orcamento_max:
            fora.append((p, score_val))
        else:
            dentro.append((p, score_val))
    # Ordena por score desc (-x[1]) e preço asc (x[0].precio)
    dentro.sort(key=lambda x: (-x[1], x[0].precio))
    fora.sort(key=lambda x: (-x[1], x[0].precio))
    return [p for p, _ in dentro + fora]


def count_good_options(scores: Dict[str, ScoreProducto], threshold: float = 2.0) -> int:
    """
    Conta quantos produtos têm score >= threshold.
    Usado para verificar se há "boas opções" suficientes no resultado LAYA.
    """
    return sum(1 for s in scores.values() if s.score >= threshold)


def top_n(productos: List[Producto], scores: Dict[str, ScoreProducto], n: int = 8, min_score: float = 1.0) -> List[Producto]:
    """
    Retorna os top N produtos ranqueados que atendem ao score mínimo.
    Usa rank_productos para ordenar e filtra por min_score.
    """
    ranked = rank_productos(productos, scores)
    return [p for p in ranked if scores.get(p.id, ScoreProducto(producto_id=p.id, score=0, probabilities={}, confidence=0)).score >= min_score][:n]


def over_budget_suggestions(productos: List[Producto], scores: Dict[str, ScoreProducto], orcamento_max: Optional[float], max_items: int = 3, min_score: float = 1.5) -> List[Producto]:
    """
    Retorna sugestões de produtos acima do orçamento que ainda têm bom score.
    Útil para mostrar alternativas premium ao usuário.
    Filtra por preço > orcamento_max e score >= min_score, ordena por score desc e preço asc.
    """
    if orcamento_max is None:
        return []
    filtered = [p for p in productos if p.precio > orcamento_max and scores.get(p.id, ScoreProducto(producto_id=p.id, score=0, probabilities={}, confidence=0)).score >= min_score]
    filtered.sort(key=lambda p: (-scores[p.id].score, p.precio))
    return filtered[:max_items]
