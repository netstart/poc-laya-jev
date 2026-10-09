#!/usr/bin/env python3
"""
LAYA Agent Runner - Script de execução do agente LAYA.

Uso:
    python scripts/run_agent.py --goal "Pesquisar por LAYA no Google" --max-steps 10
    python scripts/run_agent.py --task-file tasks.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Adiciona src ao path para imports locais
sys.path.insert(0, str(Path(__file__).parent.parent))

from laya_ultrafast.agent import LayaAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LAYA Agent Runner - Executa automação web local",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python scripts/run_agent.py --goal "Pesquisar por LAYA no Google" --max-steps 10
  python scripts/run_agent.py --goal "Preencher formulário de contato" --url "https://example.com/contact"
  python scripts/run_agent.py --task-file tasks.json --verbose
        """,
    )

    parser.add_argument("--goal", "-g", help="Meta em linguagem natural a alcançar")
    parser.add_argument(
        "--max-steps", "-m", type=int, default=25, help="Máximo de passos (default: 25)"
    )
    parser.add_argument(
        "--url",
        "-u",
        default="https://example.com",
        help="URL inicial (default: https://example.com)",
    )
    parser.add_argument("--session-id", "-s", help="ID de sessão para resumir execução anterior")
    parser.add_argument("--task-file", "-t", help="Arquivo JSON com múltiplos objetivos")
    parser.add_argument("--verbose", "-v", action="store_true", help="Habilita logging detalhado")
    parser.add_argument("--debug", "-d", action="store_true", help="Habilita debug adicional")
    parser.add_argument("--model", help="Override do modelo (ex: default para modo heurístico)")
    parser.add_argument(
        "--provider", choices=["openai", "local"], help="Override do provedor (default: local)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Executa navegador em modo headless (default: True)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_false",
        dest="headless",
        help="Executa navegador com UI visível",
    )

    return parser.parse_args()


async def run_single_goal(args: argparse.Namespace) -> int:
    """Executa um único objetivo."""
    agent = LayaAgent()

    # Aplica overrides de CLI se fornecidos
    if args.model:
        agent.config.model_name = args.model
    if args.provider:
        agent.config.model_provider = args.provider
    agent.config.browser_headless = args.headless

    result = await agent.engine.run(
        goal=args.goal,
        max_steps=args.max_steps,
        session_id=args.session_id,
        initial_url=args.url,
    )

    if result.success:
        print(f"\n✅ SUCESSO: {result.final_message}")
        print(f"   Passos: {result.steps_taken}")
        return 0
    else:
        print(f"\n❌ FALHA: {result.final_message}")
        if result.error:
            print(f"   Erro: {result.error}")
        print(f"   Passos: {result.steps_taken}")
        return 1


async def run_task_file(args: argparse.Namespace) -> int:
    """Executa múltiplos objetivos de arquivo JSON."""
    task_path = Path(args.task_file)
    if not task_path.exists():
        print(f"❌ Arquivo não encontrado: {args.task_file}")
        return 1

    with open(task_path) as f:
        tasks = json.load(f)

    if not isinstance(tasks, list):
        print("❌ Arquivo deve conter uma lista de objetos")
        return 1

    agent = LayaAgent()
    if args.model:
        agent.config.model_name = args.model
    if args.provider:
        agent.config.model_provider = args.provider
    agent.config.browser_headless = args.headless

    all_success = True

    for i, task in enumerate(tasks):
        goal = task.get("goal") or task.get("description", "")
        max_steps = task.get("max_steps", args.max_steps)
        url = task.get("url", args.url)

        if not goal:
            print(f"⚠️  Task {i + 1}: sem goal, pulando")
            continue

        print(f"\n{'=' * 50}")
        print(f"TASK {i + 1}/{len(tasks)}: {goal}")
        print(f"{'=' * 50}")

        result = await agent.engine.run(
            goal=goal,
            max_steps=max_steps,
            initial_url=url,
        )

        if result.success:
            print(f"✅ SUCESSO: {result.final_message}")
        else:
            print(f"❌ FALHA: {result.final_message}")
            if result.error:
                print(f"   Erro: {result.error}")
            all_success = False

    return 0 if all_success else 1


async def main() -> int:
    args = parse_args()

    if not args.goal and not args.task_file:
        print("❌ Erro: forneça --goal ou --task-file")
        return 1

    try:
        if args.task_file:
            return await run_task_file(args)
        else:
            return await run_single_goal(args)
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")
        return 130
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
