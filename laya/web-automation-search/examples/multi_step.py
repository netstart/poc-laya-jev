#!/usr/bin/env python3
"""
Exemplo 3: Fluxo Multi-Etapa com Checkpoints

Demonstra execução de fluxo complexo com salvamento/restauração de checkpoints.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from laya_ultrafast.agent import LayaAgent
from laya_ultrafast.core.context_manager import ContextManager, SessionContext


async def main():
    agent = LayaAgent()
    # Checkpoint automático a cada 3 passos
    agent.engine.context_manager = ContextManager(checkpoint_interval_steps=3)

    # Meta multi-etapa
    goal = """
    1. Acesse https://github.com/trending
    2. Role para baixo para ver mais repositórios
    3. Clique no primeiro repositório da lista
    4. Na página do repo, clique na aba 'Issues'
    5. Verifique se há issues abertas
    """

    print(f"🎯 Objetivo: {goal.strip()}")
    print("=" * 60)

    # Executa com checkpoint automático
    result = await agent.engine.run(
        goal=goal,
        max_steps=20,
        initial_url="https://github.com/trending",
    )

    print(f"\n{'✅ SUCESSO' if result.success else '❌ FALHA'}: {result.final_message}")
    print(f"Passos executados: {result.steps_taken}")

    # Demonstra checkpoint/restore
    if agent.engine.context_manager.get_session(result.session_id):
        session = agent.engine.context_manager.get_session(result.session_id)
        checkpoint = session.to_checkpoint()
        print(f"\n💾 Checkpoint salvo ({len(checkpoint)} bytes)")

        # Restaura sessão
        restored = SessionContext.from_checkpoint(checkpoint)
        print(f"🔄 Sessão restaurada: step {restored.current_step}/{restored.max_steps}")
        print(f"   Histórico: {len(restored.history)} passos")

    if result.metrics:
        print("\nMétricas:")
        print(f"  Tempo total: {result.metrics.get('duration_ms', 0):.0f}ms")
        print(f"  Taxa de sucesso: {result.metrics.get('success_rate', 0):.1%}")


if __name__ == "__main__":
    asyncio.run(main())
