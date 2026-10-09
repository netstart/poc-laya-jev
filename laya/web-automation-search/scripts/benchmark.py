#!/usr/bin/env python3
"""
LAYA Benchmark Runner - Executa benchmarks de performance.

Uso:
    python scripts/benchmark.py --scenario search
    python scripts/benchmark.py --all --output benchmarks/results.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from laya_ultrafast.agent import LayaAgent
from laya_ultrafast.utils.metrics import configure_metrics


@dataclass
class BenchmarkResult:
    """Resultado de um benchmark."""

    scenario: str
    success: bool
    duration_ms: float
    steps: int
    tokens_prompt: int
    tokens_completion: int
    snapshot_time_ms: float
    inference_time_ms: float
    execution_time_ms: float
    error: str | None = None


# Cenários de benchmark
SCENARIOS = {
    "search": {
        "name": "Wikipedia Search",
        "goal": "Acesse https://wikipedia.org e pesquise por 'LAYA automação'",
        "url": "https://wikipedia.org",
        "max_steps": 10,
        "expected_actions": ["TYPE_TEXT", "CLICK", "WAIT"],
    },
    "form_filling": {
        "name": "Form Filling",
        "goal": "Preencha o formulário de contato com nome, email e mensagem",
        "url": "https://httpbin.org/forms/post",
        "max_steps": 15,
        "expected_actions": ["TYPE_TEXT", "TYPE_TEXT", "TYPE_TEXT", "CLICK"],
    },
    "navigation": {
        "name": "Multi-page Navigation",
        "goal": "Navegue da home do GitHub para a página de trending e depois para um repositório",
        "url": "https://github.com",
        "max_steps": 12,
        "expected_actions": ["CLICK", "CLICK", "SCROLL_DOWN"],
    },
    "dynamic_content": {
        "name": "Dynamic Content (AJAX)",
        "goal": "Aguarde carregar resultados de busca e clique no primeiro resultado",
        "url": "https://duckduckgo.com/?q=LAYA+automation",
        "max_steps": 10,
        "expected_actions": ["WAIT", "CLICK"],
    },
    "heavy_dom": {
        "name": "Heavy DOM (>2000 elements)",
        "goal": "Encontre e clique no link 'Documentation' no final da página",
        "url": "https://developer.mozilla.org/en-US/",
        "max_steps": 15,
        "expected_actions": ["SCROLL_DOWN", "SCROLL_DOWN", "CLICK"],
    },
}


async def run_scenario(
    agent: LayaAgent,
    scenario: dict[str, Any],
    runs: int = 3,
) -> list[BenchmarkResult]:
    """Executa cenário múltiplas vezes."""
    results = []

    for run in range(runs):
        print(f"  Run {run + 1}/{runs}...", end=" ", flush=True)

        start_time = time.time()
        try:
            result = await agent.engine.run(
                goal=scenario["goal"],
                max_steps=scenario["max_steps"],
                initial_url=scenario["url"],
            )

            duration = (time.time() - start_time) * 1000

            # Extrai métricas do motor
            metrics = result.metrics or {}
            bench_result = BenchmarkResult(
                scenario=scenario["name"],
                success=result.success,
                duration_ms=duration,
                steps=result.steps_taken,
                tokens_prompt=metrics.get("tokens_prompt", 0),
                tokens_completion=metrics.get("tokens_completion", 0),
                snapshot_time_ms=metrics.get("snapshot_time_ms", 0),
                inference_time_ms=metrics.get("inference_time_ms", 0),
                execution_time_ms=metrics.get("execution_time_ms", 0),
                error=None if result.success else result.error,
            )
            results.append(bench_result)
            print("✅" if result.success else "❌")

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            bench_result = BenchmarkResult(
                scenario=scenario["name"],
                success=False,
                duration_ms=duration,
                steps=0,
                tokens_prompt=0,
                tokens_completion=0,
                snapshot_time_ms=0,
                inference_time_ms=0,
                execution_time_ms=0,
                error=str(e),
            )
            results.append(bench_result)
            print(f"💥 {e}")

    return results


def summarize_results(results: list[BenchmarkResult]) -> dict[str, Any]:
    """Sumariza resultados de múltiplas execuções."""
    if not results:
        return {}

    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    def stats(values: list[float]) -> dict[str, float]:
        if not values:
            return {"min": 0, "max": 0, "mean": 0, "median": 0, "stdev": 0}
        return {
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0,
        }

    return {
        "total_runs": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / len(results) * 100,
        "duration_ms": stats([r.duration_ms for r in successful]),
        "steps": stats([r.steps for r in successful]),
        "tokens_prompt": stats([r.tokens_prompt for r in successful]),
        "tokens_completion": stats([r.tokens_completion for r in successful]),
        "snapshot_time_ms": stats([r.snapshot_time_ms for r in successful]),
        "inference_time_ms": stats([r.inference_time_ms for r in successful]),
        "execution_time_ms": stats([r.execution_time_ms for r in successful]),
        "errors": [r.error for r in failed if r.error],
    }


def print_summary(scenario_name: str, summary: dict[str, Any]):
    """Imprime sumário formatado."""
    print(f"\n{'=' * 60}")
    print(f"  {scenario_name}")
    print(f"{'=' * 60}")
    print(
        f"  Runs: {summary['total_runs']} | Sucesso: {summary['successful']} | Falhas: {summary['failed']} ({summary['success_rate']:.1f}%)"
    )

    if summary["successful"] > 0:
        print("\n  ⏱️  Duração (ms):")
        d = summary["duration_ms"]
        print(
            f"      Média: {d['mean']:.0f} | Mediana: {d['median']:.0f} | Min: {d['min']:.0f} | Max: {d['max']:.0f} | Std: {d['stdev']:.0f}"
        )

        print("\n  📝 Passos:")
        s = summary["steps"]
        print(f"      Média: {s['mean']:.1f} | Mediana: {s['median']:.1f}")

        print("\n  🔤 Tokens:")
        tp = summary["tokens_prompt"]
        tc = summary["tokens_completion"]
        print(f"      Prompt: méd {tp['mean']:.0f} | Completion: méd {tc['mean']:.0f}")

        print("\n  ⚡ Tempos de fase (ms):")
        for phase in ["snapshot_time_ms", "inference_time_ms", "execution_time_ms"]:
            if phase in summary:
                st = summary[phase]
                label = phase.replace("_time_ms", "").replace("_", " ").title()
                print(f"      {label}: méd {st['mean']:.0f} | med {st['median']:.0f}")

    if summary["errors"]:
        print("\n  ❌ Erros:")
        for err in summary["errors"]:
            print(f"      - {err}")


async def main():
    parser = argparse.ArgumentParser(description="LAYA Benchmark Runner")
    parser.add_argument(
        "--scenario",
        "-s",
        choices=[*list(SCENARIOS.keys()), "all"],
        default="all",
        help="Cenário a executar (default: all)",
    )
    parser.add_argument(
        "--runs", "-r", type=int, default=3, help="Número de execuções por cenário (default: 3)"
    )
    parser.add_argument("--output", "-o", help="Arquivo JSON para salvar resultados")
    parser.add_argument("--model", help="Override do modelo")
    parser.add_argument(
        "--provider", choices=["ollama", "openai", "local"], help="Override do provedor"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--no-headless",
        action="store_false",
        dest="headless",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
    )

    args = parser.parse_args()

    # Configura métricas
    configure_metrics(enabled=True)

    # Cria agente
    agent = LayaAgent()
    if args.model:
        agent.config.model_name = args.model
    if args.provider:
        agent.config.model_provider = args.provider
    agent.config.browser_headless = args.headless

    # Determina cenários
    if args.scenario == "all":
        scenarios_to_run = list(SCENARIOS.values())
    else:
        scenarios_to_run = [SCENARIOS[args.scenario]]

    print(f"🚀 LAYA Benchmark - {len(scenarios_to_run)} cenário(s), {args.runs} execução(ões) cada")
    print(f"   Modelo: {agent.config.model_name} ({agent.config.model_provider})")
    print(f"   Headless: {agent.config.browser_headless}")

    all_results = {}

    for scenario in scenarios_to_run:
        print(f"\n▶️  {scenario['name']}")
        results = await run_scenario(agent, scenario, args.runs)
        summary = summarize_results(results)
        all_results[scenario["name"]] = {
            "runs": [asdict(r) for r in results],
            "summary": summary,
        }
        print_summary(scenario["name"], summary)

    # Sumário geral
    print(f"\n{'=' * 60}")
    print("  RESUMO GERAL")
    print(f"{'=' * 60}")

    total_runs = sum(s["summary"]["total_runs"] for s in all_results.values())
    total_success = sum(s["summary"]["successful"] for s in all_results.values())
    print(
        f"Total: {total_runs} runs | Sucesso: {total_success} ({total_success / total_runs * 100:.1f}%)"
    )

    for name, data in all_results.items():
        s = data["summary"]
        status = "✅" if s["success_rate"] == 100 else "⚠️" if s["success_rate"] > 50 else "❌"
        print(
            f"  {status} {name}: {s['success_rate']:.1f}% sucesso, {s['duration_ms'].get('mean', 0):.0f}ms médio"
        )

    # Salva resultados se solicitado
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Resultados salvos em: {output_path}")

    return 0 if total_success == total_runs else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
