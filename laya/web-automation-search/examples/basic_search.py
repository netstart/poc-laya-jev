#!/usr/bin/env python3
"""
Exemplo 1: Busca Básica na Wikipedia

Demonstra uso básico do agente LAYA para pesquisar na Wikipedia.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from laya_ultrafast.agent import LayaAgent


async def main():
    agent = LayaAgent()

    # Objetivo: pesquisar na Wikipedia
    goal = "Acesse a Wikipedia e pesquise por 'LAYA automação web'. Clique no primeiro resultado."

    print(f"🎯 Objetivo: {goal}")
    print("=" * 60)

    result = await agent.engine.run(
        goal=goal,
        max_steps=10,
        initial_url="https://wikipedia.org",
    )

    print(f"\n{'✅ SUCESSO' if result.success else '❌ FALHA'}: {result.final_message}")
    print(f"Passos executados: {result.steps_taken}")

    if result.metrics:
        print("\nMétricas:")
        print(f"  Tempo total: {result.metrics.get('duration_ms', 0):.0f}ms")
        print(f"  Taxa de sucesso: {result.metrics.get('success_rate', 0):.1%}")


if __name__ == "__main__":
    asyncio.run(main())
