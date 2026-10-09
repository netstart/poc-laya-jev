from __future__ import annotations

import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class Timer:
    """Timer simples para medir duração."""

    name: str
    start_time: float = field(default_factory=time.perf_counter)
    end_time: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def stop(self) -> float:
        self.end_time = time.perf_counter()
        return self.duration_ms

    @property
    def duration_ms(self) -> float:
        end = self.end_time or time.perf_counter()
        return (end - self.start_time) * 1000

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stop()


@dataclass(slots=True)
class MetricPoint:
    """Ponto de métrica individual."""

    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Coletor de métricas em memória com agregação estatística.

    Thread-safe para uso assíncrono.
    """

    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._lock = threading.RLock()
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._timers: dict[str, Timer] = {}
        self._points: list[MetricPoint] = []
        self._max_points = 10000

    def increment(self, name: str, value: float = 1.0, tags: dict[str, str] | None = None):
        if not self._enabled:
            return
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] += value
            self._record_point(name, value, tags)

    def gauge(self, name: str, value: float, tags: dict[str, str] | None = None):
        if not self._enabled:
            return
        with self._lock:
            key = self._make_key(name, tags)
            self._gauges[key] = value
            self._record_point(name, value, tags)

    def histogram(self, name: str, value: float, tags: dict[str, str] | None = None):
        if not self._enabled:
            return
        with self._lock:
            key = self._make_key(name, tags)
            self._histograms[key].append(value)
            # Limita tamanho do histograma
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
            self._record_point(name, value, tags)

    def timing(self, name: str, duration_ms: float, tags: dict[str, str] | None = None):
        """Registra tempo de duração."""
        self.histogram(f"{name}.duration_ms", duration_ms, tags)

    def start_timer(self, name: str, metadata: dict[str, Any] | None = None) -> Timer:
        timer = Timer(name=name, metadata=metadata or {})
        with self._lock:
            self._timers[name] = timer
        return timer

    def stop_timer(self, name: str, tags: dict[str, str] | None = None) -> float | None:
        with self._lock:
            timer = self._timers.pop(name, None)
        if timer:
            duration = timer.stop()
            self.timing(name, duration, tags)
            return duration
        return None

    @contextmanager
    def measure(self, name: str, tags: dict[str, str] | None = None):
        """Context manager para medir duração de bloco."""
        timer = self.start_timer(name)
        try:
            yield timer
        finally:
            self.stop_timer(name, tags)

    def _make_key(self, name: str, tags: dict[str, str] | None) -> str:
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"

    def _record_point(self, name: str, value: float, tags: dict[str, str] | None):
        self._points.append(MetricPoint(name=name, value=value, tags=tags or {}))
        if len(self._points) > self._max_points:
            self._points = self._points[-self._max_points :]

    def get_counter(self, name: str, tags: dict[str, str] | None = None) -> float:
        with self._lock:
            return self._counters.get(self._make_key(name, tags), 0.0)

    def get_gauge(self, name: str, tags: dict[str, str] | None = None) -> float | None:
        with self._lock:
            return self._gauges.get(self._make_key(name, tags))

    def get_histogram_stats(
        self, name: str, tags: dict[str, str] | None = None
    ) -> dict[str, float]:
        with self._lock:
            values = self._histograms.get(self._make_key(name, tags), [])
        if not values:
            return {"count": 0, "min": 0, "max": 0, "mean": 0, "p50": 0, "p95": 0, "p99": 0}
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        return {
            "count": n,
            "min": sorted_vals[0],
            "max": sorted_vals[-1],
            "mean": sum(sorted_vals) / n,
            "p50": sorted_vals[int(n * 0.5)],
            "p95": sorted_vals[int(n * 0.95)] if n > 1 else sorted_vals[0],
            "p99": sorted_vals[int(n * 0.99)] if n > 1 else sorted_vals[0],
        }

    def get_all_counters(self) -> dict[str, float]:
        with self._lock:
            return dict(self._counters)

    def get_all_gauges(self) -> dict[str, float]:
        with self._lock:
            return dict(self._gauges)

    def get_all_histograms(self) -> dict[str, dict[str, float]]:
        with self._lock:
            return {
                k: {
                    "count": len(v),
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                    "mean": sum(v) / len(v) if v else 0,
                }
                for k, v in self._histograms.items()
            }

    def snapshot(self) -> dict[str, Any]:
        """Retorna snapshot completo das métricas."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    k: {
                        "count": len(v),
                        "min": min(v) if v else 0,
                        "max": max(v) if v else 0,
                        "mean": sum(v) / len(v) if v else 0,
                    }
                    for k, v in self._histograms.items()
                },
                "points_count": len(self._points),
            }

    def reset(self):
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
            self._points.clear()


# Instância global
_metrics: MetricsCollector | None = None
_metrics_lock = threading.Lock()


def get_metrics() -> MetricsCollector:
    global _metrics
    if _metrics is None:
        with _metrics_lock:
            if _metrics is None:
                _metrics = MetricsCollector()
    return _metrics


def configure_metrics(enabled: bool = True) -> MetricsCollector:
    global _metrics
    with _metrics_lock:
        _metrics = MetricsCollector(enabled=enabled)
    return _metrics


#: Helpers convenientes


def increment(name: str, value: float = 1.0, tags: dict[str, str] | None = None) -> None:
    """Incrementa um contador global."""
    get_metrics().increment(name, value, tags)


def gauge(name: str, value: float, tags: dict[str, str] | None = None) -> None:
    """Define um gauge global."""
    get_metrics().gauge(name, value, tags)


def histogram(name: str, value: float, tags: dict[str, str] | None = None) -> None:
    """Registra uma observação em histograma global."""
    get_metrics().histogram(name, value, tags)


@contextmanager
def timing(name: str, tags: dict[str, str] | None = None) -> Iterator[Timer]:
    """Mede a duração do bloco e grava em ``{name}.duration_ms``.

    Uso::

        with timing("snapshot.capture"):
            ...
    """
    with get_metrics().measure(name, tags) as timer:
        yield timer


@contextmanager
def measure(name: str, tags: dict[str, str] | None = None) -> Iterator[Timer]:
    """Alias explícito de :func:`timing` (mantido por compatibilidade)."""
    with get_metrics().measure(name, tags) as timer:
        yield timer
