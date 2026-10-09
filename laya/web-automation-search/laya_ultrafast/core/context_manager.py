from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog

from laya_ultrafast.core.action_executor import Action, ExecutionResult
from laya_ultrafast.core.exceptions import CheckpointError, SessionExpiredError
from laya_ultrafast.utils.dom import ElementSnapshot

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class StepRecord:
    """Registro de um passo da execução."""

    step: int
    timestamp: float
    snapshot_id: str
    action: Action
    result: ExecutionResult
    goal: str
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "timestamp": self.timestamp,
            "snapshot_id": self.snapshot_id,
            "action": self.action.to_dict(),
            "result": self.result.to_dict(),
            "goal": self.goal,
            "metrics": self.metrics,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StepRecord:
        return cls(
            step=data["step"],
            timestamp=data["timestamp"],
            snapshot_id=data["snapshot_id"],
            action=Action.from_dict(data["action"]),
            result=ExecutionResult(
                success=data["result"]["success"],
                action=Action.from_dict(data["result"]["action"]),
                message=data["result"].get("message", ""),
                error=data["result"].get("error"),
                new_snapshot_id=data["result"].get("new_snapshot_id"),
                metadata=data["result"].get("metadata", {}),
            ),
            goal=data["goal"],
            metrics=data.get("metrics", {}),
        )


@dataclass(slots=True)
class SessionContext:
    """
    Contexto completo de uma sessão do agente.

    Mantém histórico, snapshots, decisões e métricas para:
    - Debugging e análise pós-execução
    - Checkpoint/resume
    - Métricas de performance
    """

    session_id: str
    goal: str
    created_at: float
    updated_at: float
    max_steps: int
    current_step: int = 0
    snapshots: dict[str, list[ElementSnapshot]] = field(default_factory=dict)
    history: list[StepRecord] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    ttl_seconds: int = 3600  # 1 hora default

    def add_step(
        self,
        snapshot_id: str,
        action: Action,
        result: ExecutionResult,
        snapshot: list[ElementSnapshot],
        step_metrics: dict[str, Any] | None = None,
    ) -> StepRecord:
        """Adiciona um passo ao histórico."""
        self.current_step += 1
        record = StepRecord(
            step=self.current_step,
            timestamp=time.time(),
            snapshot_id=snapshot_id,
            action=action,
            result=result,
            goal=self.goal,
            metrics=step_metrics or {},
        )
        self.history.append(record)
        self.snapshots[snapshot_id] = snapshot
        self.updated_at = time.time()
        return record

    def get_latest_snapshot(self) -> list[ElementSnapshot] | None:
        """Retorna o snapshot mais recente."""
        if not self.history:
            return None
        latest_id = self.history[-1].snapshot_id
        return self.snapshots.get(latest_id)

    def get_snapshot(self, snapshot_id: str) -> list[ElementSnapshot] | None:
        return self.snapshots.get(snapshot_id)

    def get_history_summary(self, last_n: int = 5) -> list[dict[str, Any]]:
        """Retorna resumo dos últimos N passos."""
        return [r.to_dict() for r in self.history[-last_n:]]

    def is_expired(self) -> bool:
        return time.time() - self.updated_at > self.ttl_seconds

    def steps_remaining(self) -> int:
        return max(0, self.max_steps - self.current_step)

    def can_continue(self) -> bool:
        return self.current_step < self.max_steps and not self.is_expired()

    def to_checkpoint(self) -> bytes:
        """Serializa sessão para checkpoint."""
        try:
            data = {
                "session_id": self.session_id,
                "goal": self.goal,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "max_steps": self.max_steps,
                "current_step": self.current_step,
                "snapshots": {k: [s.to_dict() for s in v] for k, v in self.snapshots.items()},
                "history": [r.to_dict() for r in self.history],
                "metrics": self.metrics,
                "metadata": self.metadata,
                "ttl_seconds": self.ttl_seconds,
            }
            return json.dumps(data, ensure_ascii=False).encode("utf-8")
        except Exception as e:
            raise CheckpointError(f"Failed to serialize checkpoint: {e}") from e

    @classmethod
    def from_checkpoint(cls, data: bytes) -> SessionContext:
        """Restaura sessão a partir de checkpoint."""
        try:
            obj = json.loads(data.decode("utf-8"))
            session = cls(
                session_id=obj["session_id"],
                goal=obj["goal"],
                created_at=obj["created_at"],
                updated_at=obj["updated_at"],
                max_steps=obj["max_steps"],
                current_step=obj["current_step"],
                snapshots={
                    k: [ElementSnapshot.from_dict(s) for s in v]
                    for k, v in obj["snapshots"].items()
                },
                history=[StepRecord.from_dict(r) for r in obj["history"]],
                metrics=obj.get("metrics", {}),
                metadata=obj.get("metadata", {}),
                ttl_seconds=obj.get("ttl_seconds", 3600),
            )

            if session.is_expired():
                raise SessionExpiredError(f"Session {session.session_id} has expired")

            return session
        except SessionExpiredError:
            raise
        except Exception as e:
            raise CheckpointError(f"Failed to restore checkpoint: {e}") from e

    def to_summary_dict(self) -> dict[str, Any]:
        """Resumo para logging/debug."""
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "current_step": self.current_step,
            "max_steps": self.max_steps,
            "snapshots_count": len(self.snapshots),
            "history_length": len(self.history),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_expired": self.is_expired(),
            "metrics": self.metrics,
        }


class ContextManager:
    """
    Gerenciador de contextos de sessão.

    Funcionalidades:
    - Criação de novas sessões
    - Checkpoint automático periódico
    - Restauração de sessões
    - Limpeza de sessões expiradas (TTL)
    """

    def __init__(
        self,
        checkpoint_interval_steps: int = 5,
        default_ttl_seconds: int = 3600,
        max_sessions: int = 100,
    ):
        self.checkpoint_interval = checkpoint_interval_steps
        self.default_ttl = default_ttl_seconds
        self.max_sessions = max_sessions
        self._sessions: dict[str, SessionContext] = {}
        self._last_checkpoint_step: dict[str, int] = {}

    def create_session(
        self,
        goal: str,
        max_steps: int = 25,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionContext:
        """Cria nova sessão."""
        if len(self._sessions) >= self.max_sessions:
            self._cleanup_expired()
            if len(self._sessions) >= self.max_sessions:
                # Remove a mais antiga
                oldest_id = min(self._sessions.keys(), key=lambda k: self._sessions[k].created_at)
                del self._sessions[oldest_id]
                logger.warning("Removed oldest session due to limit", session_id=oldest_id)

        session = SessionContext(
            session_id=session_id or str(uuid.uuid4())[:8],
            goal=goal,
            created_at=time.time(),
            updated_at=time.time(),
            max_steps=max_steps,
            ttl_seconds=self.default_ttl,
            metadata=metadata or {},
        )
        self._sessions[session.session_id] = session
        self._last_checkpoint_step[session.session_id] = 0
        logger.info("Session created", session_id=session.session_id, goal=goal)
        return session

    def get_session(self, session_id: str) -> SessionContext | None:
        """Obtém sessão por ID."""
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            self._remove_session(session_id)
            return None
        return session

    def update_session(self, session: SessionContext):
        """Atualiza sessão (checkpoint automático se necessário)."""
        self._sessions[session.session_id] = session
        self._maybe_checkpoint(session)

    def _maybe_checkpoint(self, session: SessionContext):
        """Faz checkpoint se intervalo atingido."""
        last = self._last_checkpoint_step.get(session.session_id, 0)
        if session.current_step - last >= self.checkpoint_interval:
            self._last_checkpoint_step[session.session_id] = session.current_step
            # Checkpoint seria salvo em disco aqui se necessário
            logger.debug(
                "Auto-checkpoint", session_id=session.session_id, step=session.current_step
            )

    def save_checkpoint(self, session_id: str) -> bytes | None:
        """Salva checkpoint da sessão."""
        session = self.get_session(session_id)
        if not session:
            return None
        return session.to_checkpoint()

    def restore_session(self, checkpoint_data: bytes) -> SessionContext:
        """Restaura sessão a partir de checkpoint."""
        session = SessionContext.from_checkpoint(checkpoint_data)
        self._sessions[session.session_id] = session
        self._last_checkpoint_step[session.session_id] = session.current_step
        logger.info("Session restored", session_id=session.session_id, step=session.current_step)
        return session

    def delete_session(self, session_id: str) -> bool:
        """Remove sessão."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._last_checkpoint_step.pop(session_id, None)
            logger.info("Session deleted", session_id=session_id)
            return True
        return False

    def _remove_session(self, session_id: str):
        self._sessions.pop(session_id, None)
        self._last_checkpoint_step.pop(session_id, None)

    def _cleanup_expired(self):
        """Remove sessões expiradas."""
        expired = [sid for sid, session in self._sessions.items() if session.is_expired()]
        for sid in expired:
            self._remove_session(sid)
        if expired:
            logger.info("Cleaned up expired sessions", count=len(expired))

    def list_sessions(self) -> list[dict[str, Any]]:
        """Lista todas as sessões ativas."""
        self._cleanup_expired()
        return [s.to_summary_dict() for s in self._sessions.values()]

    def get_session_count(self) -> int:
        return len(self._sessions)

    def clear_all(self):
        """Remove todas as sessões."""
        count = len(self._sessions)
        self._sessions.clear()
        self._last_checkpoint_step.clear()
        logger.info("All sessions cleared", count=count)
