#!/usr/bin/env python3
import time
import json
import statistics
from pathlib import Path
from app.laya_engine import LayaEngine
from app.schemas import Producto
from app.main import load_catalogo

CHECKPOINT = "laya-multilingual"
DEVICE = "cpu"
BATCH_SIZES = [1, 5, 24, 50, 120, 125]
REPEATS = 10


def load_products(n: int = 120) -> list[Producto]:
    prods = load_catalogo()
    return prods[: min(n, len(prods))]


def benchmark():
    engine = LayaEngine(checkpoint=CHECKPOINT, device=DEVICE)
    productos = load_products()
    query = "presente pra minha mãe que ama jardinagem até 150 reais"

    results = []
    for size in BATCH_SIZES:
        times = []
        for _ in range(REPEATS):
            subset = productos[:size]
            t0 = time.perf_counter()
            engine.score_products(query, subset)
            dt = (time.perf_counter() - t0) * 1000
            times.append(dt)
        results.append({
            "batch_size": size,
            "p50_ms": round(statistics.median(times), 2),
            "p90_ms": round(statistics.quantiles(times, n=10)[8], 2) if len(times) >= 10 else round(max(times), 2),
            "p95_ms": round(statistics.quantiles(times, n=20)[18], 2) if len(times) >= 20 else round(max(times), 2),
            "max_ms": round(max(times), 2),
            "min_ms": round(min(times), 2),
        })

    out = Path("data-runtime") / "benchmark.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"checkpoint": CHECKPOINT, "device": DEVICE, "results": results}, f, indent=2)
    print(json.dumps({"checkpoint": CHECKPOINT, "device": DEVICE, "results": results}, indent=2))


if __name__ == "__main__":
    benchmark()
