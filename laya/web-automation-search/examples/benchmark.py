#!/usr/bin/env python3
"""
Exemplo 4: Benchmark Personalizado

Executa benchmarks customizados e compara com baseline.
"""

from __future__ import annotations

import asyncio
import json
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from laya_ultrafast.agent import LayaAgent
from laya_ultrafast.utils.metrics import configure_metrics


@dataclass
class BenchmarkRun:
    name: str
    goal: str
    url: str
    max_steps: int
    expected_min_success_rate: float = 0.8


CUSTOM_BENCHMARKS = [
    BenchmarkRun(
        name="Google Search",
        goal="Pesquise por 'LAYA automação' no Google",
        url="https://google.com",
        max_steps=8,
    ),
    BenchmarkRun(
        name="DuckDuckGo Search",
        goal="Pesquise por 'automação web local' no DuckDuckGo",
        url="https://duckduckgo.com",
        max_steps=8,
    ),
    BenchmarkRun(
        name="GitHub Trending",
        goal="Acesse GitHub Trending e abra o primeiro repositório",
        url="https://github.com/trending",
        max_steps=10,
    ),
]


async def run_benchmark(agent: LayaAgent, bench: BenchmarkRun, runs: int = 5) -> dict:
    """Executa benchmark múltiplas vezes."""
    durations = []
    steps_list = []
    success_count = 0
    errors = []

    print(f"\n🔬 {bench.name} ({runs} runs)")

    for i in range(runs):
        start = time.time()
        try:
            result = await agent.engine.run(
                goal=bench.goal,
                max_steps=bench.max_steps,
                initial_url=bench.url,
            )
            duration = (time.time() - start) * 1000

            durations.append(duration)
            steps_list.append(result.steps_taken)

            if result.success:
                success_count += 1
                print(f"  Run {i + 1}: ✅ {duration:.0f}ms, {result.steps_taken} passos")
            else:
                print(f"  Run {i + 1}: ❌ {duration:.0f}ms - {result.error}")
                errors.append(result.error)

        except Exception as e:
            duration = (time.time() - start) * 1000
            print(f"  Run {i + 1}: 💥 {duration:.0f}ms - {e}")
            errors.append(str(e))

    success_rate = success_count / runs

    summary = {
        "name": bench.name,
        "runs": runs,
        "success_rate": success_rate,
        "avg_duration_ms": statistics.mean(durations) if durations else 0,
        "median_duration_ms": statistics.median(durations) if durations else 0,
        "avg_steps": statistics.mean(steps_list) if steps_list else 0,
        "passed": success_rate >= bench.expected_min_success_rate,
        "errors": errors,
    }

    print(f"  📊 Taxa de sucesso: {success_rate:.1%}")
    print(f"  ⏱️  Duração média: {summary['avg_duration_ms']:.0f}ms")
    print(f"  📝 Passos médios: {summary['avg_steps']:.1f}")
    print(
        f"  {'✅ PASSOU' if summary['passed'] else '❌ FALHOU'} (threshold: {bench.expected_min_success_rate:.0%})"
    )

    return summary


async def main():
    configure_metrics(enabled=True)

    agent = LayaAgent()
    print("🚀 LAYA Custom Benchmark")
    print("=" * 50)

    all_results = []

    for bench in CUSTOM_BENCHMARKS:
        result = await run_benchmark(agent, bench, runs=3)
        all_results.append(result)

    # Sumário final
    print("\n" + "=" * 50)
    print("RESUMO FINAL")
    print("=" * 50)

    all_passed = all(r["passed"] for r in all_results)

    for r in all_results:
        status = "✅" if r["passed"] else "❌"
        print(
            f"  {status} {r['name']}: {r['success_rate']:.1%} sucesso, {r['avg_duration_ms']:.0f}ms"
        )

    # Salva resultados
    output = {
        "timestamp": time.time(),
        "model": agent.config.model_name,
        "provider": agent.config.model_provider,
        "results": all_results,
        "overall_passed": all_passed,
    }

    output_path = Path("benchmarks/custom_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Resultados salvos em: {output_path}")
    print(
        f"\n{'🎉 TODOS OS BENCHMARKS PASSARAM' if all_passed else '⚠️  ALGUNS BENCHMARKS FALHARAM'}"
    )

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
