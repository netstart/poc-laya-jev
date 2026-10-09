#!/usr/bin/env python3
"""
Exemplo 2: Preenchimento de Formulário

Demonstra preenchimento de formulário complexo com múltiplos campos.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from laya_ultrafast.agent import LayaAgent


async def main():
    agent = LayaAgent()

    # Objetivo: preencher formulário
    goal = """
    Preencha o formulário de contato com:
    - Nome: 'João Silva'
    - Email: 'joao@exemplo.com'
    - Assunto: 'Teste LAYA'
    - Mensagem: 'Este é um teste de automação com o agente LAYA.'
    Em seguida, clique no botão de envio.
    """

    print(f"🎯 Objetivo: {goal.strip()}")
    print("=" * 60)

    result = await agent.engine.run(
        goal=goal,
        max_steps=15,
        initial_url="https://httpbin.org/forms/post",
    )

    print(f"\n{'✅ SUCESSO' if result.success else '❌ FALHA'}: {result.final_message}")
    print(f"Passos executados: {result.steps_taken}")

    if result.metrics:
        print("\nMétricas:")
        print(f"  Tempo total: {result.metrics.get('duration_ms', 0):.0f}ms")
        print(f"  Taxa de sucesso: {result.metrics.get('success_rate', 0):.1%}")


if __name__ == "__main__":
    asyncio.run(main())
