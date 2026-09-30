import re
import math
import time
from typing import List, Dict, Optional
from app.schemas import Producto
from app.laya_engine import LayaEngine
from app.ranking import rank_productos, count_good_options, top_n, over_budget_suggestions
from app.cache import get_cache
from app.orcamento import bucket_budget


STOPWORDS = {"de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "com", "nao", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", "mas", "ao", "ele", "das", "seu", "sua", "ou", "quando", "muito", "nos", "ja", "eu", "tambem", "so", "pelo", "pela", "ate", "isso", "ela", "entre", "sem", "mesmo", "seu", "sua", "onde", "quem", "voc", "tem", "mae", "pra", "para"}


def tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    tokens = text.split()
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def keyword_search(query: str, productos: List[Producto]) -> List[Producto]:
    terms = tokenize(query)
    if not terms:
        return []
    scored = []
    for p in productos:
        text = f"{p.nombre} {p.descripcion} {' '.join(p.tags)} {p.categoria} {p.departamento}".lower()
        score = 0
        for term in terms:
            score += text.count(term)
        scored.append((p, score))
    scored.sort(key=lambda x: (-x[1], x[0].precio))
    return [p for p, s in scored if s > 0]


class SearchEngine:
    def __init__(self, productos: List[Producto], laya: LayaEngine):
        self.productos = productos
        self.laya = laya
        self.cache = get_cache()

    def buscar(self, q: str, fresh: bool = False) -> dict:
        cached = self.cache.get(q, fresh)
        if cached is not None:
            return {**cached, "cached": True}

        t0 = time.time()
        entendimiento = self.laya.understand_query(q)
        orcamento_max = entendimiento.orcamento_max

        scores_list = self.laya.score_products(q, self.productos)
        scores = {sp.producto_id: sp for sp in scores_list}
        ordem = [p.id for p in rank_productos(self.productos, scores, orcamento_max)]

        n_chamadas = 1 + (len(self.productos) + 23) // 24
        latency = int((time.time() - t0) * 1000)

        resultado = {
            "ok": True,
            "q": q,
            "cached": False,
            "entendimiento": entendimiento.model_dump() if hasattr(entendimiento, "model_dump") else {
                "pilulas": [],
                "intencion": entendimiento.intencion,
                "categoria": entendimiento.categoria,
                "destinatario": entendimiento.destinatario,
                "ocasion": entendimiento.ocasion,
                "orcamento_max": orcamento_max,
                "orcamento_fonte": entendimiento.orcamento_fonte,
                "confianca": entendimiento.confianca,
                "bruto": entendimiento.bruto,
            },
            "scores": {p.id: [s.score, s.probabilities.get("0", 0), s.probabilities.get("1", 0), s.probabilities.get("2", 0), s.probabilities.get("3", 0)] for p, s in zip(self.productos, scores_list)},
            "ordem": ordem,
            "lotes": [],
            "latency_ms": latency,
            "laya_ms": latency,
            "n_produtos": len(self.productos),
            "n_chamadas": n_chamadas,
            "n_perguntas": 5 + len(self.productos),
            "parcial": None,
            "_laya": [],
        }
        self.cache.put(q, fresh, resultado)
        return resultado
