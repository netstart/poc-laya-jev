from __future__ import annotations

import argparse
import asyncio
import json
import logging
import signal
import sys
from pathlib import Path
from typing import Any

import structlog

from laya_ultrafast import __version__
from laya_ultrafast.config.settings import get_config
from laya_ultrafast.core.exceptions import AgentError
from laya_ultrafast.core.laya_engine import LayaEngine, RunResult
from laya_ultrafast.utils.metrics import configure_metrics


class LayaAgent:
    """
    Agente LAYA de alto nível - Fachada principal para usuários.

    Responsabilidades:
    - Parâmetros da linha de comando e CLI
    - Inicialização do navegador e do modelo
    - Loop principal de execução e saída amigável
    - Tratamento de sinais (Ctrl+C)
    - Monitoramento e logging
    """

    def __init__(self):
        self.config = get_config()
        self.engine = LayaEngine()
        self.metrics_enabled = self.config.metrics_enabled
        if self.metrics_enabled:
            configure_metrics(enabled=True)

    async def run(self, args: Any) -> None:
        """
        Executa o agente de acordo com os argumentos fornecidos.

        Args:
            args: Argumentos de linha de comando do argparse.Namespace
        """
        # Configura logger
        self._setup_logging(getattr(args, "verbose", False))

        goal = getattr(args, "goal", None)
        task_file = getattr(args, "task_file", None)

        if not goal and not task_file:
            self._print_help()
            return

        # Inicializa modelo e navegador
        await self._initialize_components(args)
        try:
            if goal:
                await self._execute_goal(goal, args)
            else:
                await self._execute_tasks_from_file(task_file)
        finally:
            await self.close()

    def _setup_logging(self, verbose: bool = False) -> None:
        """Configura logging estruturado (nível controlado por ``--verbose``)."""
        level = "DEBUG" if verbose else self.config.log_level
        logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.JSONRenderer()
                if self.config.log_format == "json"
                else structlog.dev.ConsoleRenderer(),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, level.upper(), logging.INFO)
            ),
            cache_logger_on_first_use=False,
        )
        self.logger = structlog.get_logger()
        self.logger.info("LAYA agent starting", version=__version__)

    async def _initialize_components(self, args: Any) -> None:
        """Conecta o navegador (CDP) e instancia o cliente de modelo local.

        Implementa as camadas reais das §4.2 (BrowserSession) e §4.3
        (LocalModelClient) — sem mocks.
        """
        self.logger.info("Initializing components")

        headless = getattr(args, "headless", None)
        model_name = getattr(args, "model", None)
        updates = {
            key: value
            for key, value in {
                "browser_headless": headless,
                "model_name": model_name,
            }.items()
            if value is not None
        }
        if updates:
            # Config é imutável (frozen): copia com os overrides da CLI
            self.config = self.config.model_copy(update=updates)
            self.engine.config = self.config

        if self.engine.browser is None:
            from laya_ultrafast.browser import BrowserSession

            session = BrowserSession(config=self.config)
            await session.connect()
            self.engine.set_browser(session)

        if self.engine.model is None:
            from laya_ultrafast.model import create_model_client

            self.engine.set_model(create_model_client(self.config))

        self.logger.info(
            "Components initialized",
            model=self.config.model_name,
            provider=self.config.model_provider,
            headless=self.config.browser_headless,
        )

    async def close(self) -> None:
        """Libera recursos (navegador e cliente de modelo)."""
        browser = self.engine.browser
        if browser is not None and hasattr(browser, "close"):
            await browser.close()
        model = self.engine.model
        if model is not None and hasattr(model, "close"):
            await model.close()

    async def _execute_goal(self, goal: str, args: Any):
        """Executa um único objetivo."""
        self.logger.info("Executing goal", goal=goal)

        result: RunResult = await self.engine.run(
            goal=goal,
            max_steps=args.max_steps,
            session_id=args.session_id,
            initial_url=args.url,
        )

        await self._print_result(result)

    async def _execute_tasks_from_file(self, task_file: str):
        """Executa múltiplos objetivos de um arquivo."""
        path = Path(task_file)
        if not path.exists():
            raise AgentError(f"Task file not found: {task_file}")

        with open(path) as f:
            tasks = json.load(f)

        for task in tasks:
            goal = task.get("goal", task.get("description", ""))
            max_steps = task.get("max_steps", self.config.max_steps)
            await self._execute_goal(
                goal, type("Args", (), {"max_steps": max_steps, "session_id": None, "url": None})()
            )

    async def _print_result(self, result: RunResult):
        """Imprime resultado formatado."""
        if result.success:
            self.logger.info(
                "✅ Goal achieved", steps=result.steps_taken, message=result.final_message
            )
        else:
            self.logger.error(
                "❌ Goal failed",
                error=result.error,
                steps=result.steps_taken,
                message=result.final_message,
            )

        # Imprime métricas se disponível
        if result.metrics:
            print("\n=== Métricas ===")
            print(f"Tempo: {result.metrics.get('duration_ms', 0):.0f}ms")
            print(f"Passos: {result.metrics.get('steps', 0)}")
            print(f"Taxa de sucesso: {result.metrics.get('success_rate', 0):.2%}")

        # Mostra snapshot do estado final se debug
        if self.config.debug and result.session_summary:
            print(f"\nEstado final da sessão: {result.session_summary}")

    def _print_help(self):
        print("""
Uso: laya [OPÇÕES]

Executa automação web usando agentes locais LAYA (sem nuvem).

OPÇÕES:
  --goal GOAL           Meta a alcançar (ex.: "Pesquisar por 'LAYA' na Wikipedia")
  --max-steps N         Máximo de passos (default: 25)
  --url URL             URL inicial (padrão: https://example.com)
  --headless            Modo headless (use --no-headless para janela visível)
  --model NAME          Modelo local a usar (sobrepõe LAYA_MODEL_NAME)
  --session-id ID       ID de sessão para resumir execução anterior
  --task-file FILE      Executa múltiplos objetivos de um arquivo JSON
  --verbose             Logging detalhado
  --debug               Debug adicional e snapshots

Exemplos:
  laya --goal "Pesquisar por laya na Wikipedia" --max-steps 10
  laya --goal "Preencher o formulário" --url http://localhost:8000 --no-headless
  laya --task-file tasks.json

Para mais informações, visite: https://github.com/your-org/laya-ultrafast
        """)


def main():
    """Entry point CLI."""
    parser = argparse.ArgumentParser(
        description="LAYA - Agente Web Local Ultra-Rápido",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--goal", help="Meta em linguagem natural a alcançar")
    parser.add_argument(
        "--max-steps", type=int, default=None, help="Máximo de passos (default: 25)"
    )
    parser.add_argument(
        "--url", default="https://example.com", help="URL inicial (default: https://example.com)"
    )
    parser.add_argument("--session-id", help="ID de sessão para resumir execução anterior")
    parser.add_argument("--task-file", help="Arquivo JSON com múltiplos objetivos")
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Executa o navegador em modo headless (padrão: LAYA_BROWSER_HEADLESS)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Sobrepõe o modelo local (ex.: llama3.1:8b-instruct-q4_K_M)",
    )
    parser.add_argument("--verbose", action="store_true", help="Habilita logging detalhado")
    parser.add_argument("--debug", action="store_true", help="Habilita debug adicional")

    args = parser.parse_args()

    # Handler para SIGINT (Ctrl+C)
    def signal_handler(signum, frame):
        print("\n⚠️  Interrompido pelo usuário")
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, signal_handler)

    agent = LayaAgent()

    try:
        asyncio.run(agent.run(args))
    except KeyboardInterrupt:
        print("\n👋 Até logo!")
        sys.exit(0)
    except AgentError as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")
        sys.exit(2)
