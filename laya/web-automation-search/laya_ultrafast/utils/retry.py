from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from functools import wraps
from typing import TYPE_CHECKING, TypeVar

import structlog
from tenacity import (
    before_sleep,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from laya_ultrafast.core.exceptions import CircuitBreakerOpenError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = structlog.get_logger(__name__)

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Política de retry configurável."""

    max_attempts: int = 3
    base_delay_ms: int = 1000
    max_delay_ms: int = 10000
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = (
        TimeoutError,
        ConnectionError,
        IOError,
    )

    def get_tenacity_retry(self):
        """Retorna decorator tenacity configurado."""
        wait = (
            wait_exponential_jitter(
                initial=self.base_delay_ms / 1000,
                max=self.max_delay_ms / 1000,
                exp_base=self.exponential_base,
            )
            if self.jitter
            else wait_exponential_jitter(
                initial=self.base_delay_ms / 1000,
                max=self.max_delay_ms / 1000,
                exp_base=self.exponential_base,
                jitter=0,
            )
        )

        return retry(
            reraise=True,
            stop=stop_after_attempt(self.max_attempts),
            wait=wait,
            retry=retry_if_exception_type(self.retryable_exceptions),
            before_sleep=before_sleep(logger.warning, "Retrying after failure"),
        )


# Políticas pré-definidas
DEFAULT_RETRY = RetryPolicy()
FAST_RETRY = RetryPolicy(max_attempts=2, base_delay_ms=100, max_delay_ms=500)
SLOW_RETRY = RetryPolicy(max_attempts=5, base_delay_ms=2000, max_delay_ms=30000)
MODEL_RETRY = RetryPolicy(
    max_attempts=3,
    base_delay_ms=1000,
    max_delay_ms=10000,
    retryable_exceptions=(
        TimeoutError,
        ConnectionError,
        IOError,
        ValueError,  # JSON parsing errors, etc.
    ),
)
BROWSER_RETRY = RetryPolicy(
    max_attempts=3,
    base_delay_ms=500,
    max_delay_ms=5000,
    retryable_exceptions=(
        TimeoutError,
        ConnectionError,
        IOError,
        RuntimeError,  # CDP errors
    ),
)


def with_retry(policy: RetryPolicy = DEFAULT_RETRY):
    """Decorator para adicionar retry a funções assíncronas."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        @policy.get_tenacity_retry()
        async def wrapper(*args, **kwargs) -> T:
            return await func(*args, **kwargs)

        return wrapper

    return decorator


#: Tipos aceitos como ``expected_exception`` (``isinstance``-style).
ExceptionTypes = type[Exception] | tuple[Exception, ...]


class CircuitBreaker:
    """Circuit breaker para proteger contra falhas em cascata."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_ms: int = 30000,
        expected_exception: ExceptionTypes = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_ms / 1000
        self.expected_exception = expected_exception

        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._state = "closed"  # closed, open, half-open
        self._lock = asyncio.Lock()

    @property
    def state(self) -> str:
        return self._state

    async def call(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        async with self._lock:
            if self._state == "open":
                if (
                    self._last_failure_time
                    and time.time() - self._last_failure_time >= self.recovery_timeout
                ):
                    self._state = "half-open"
                    logger.info("Circuit breaker entering half-open state")
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is open. Retry after {self.recovery_timeout}s"
                    )

        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                self._on_success()
            return result
        except self.expected_exception:
            async with self._lock:
                self._on_failure()
            raise

    def _on_success(self):
        self._failure_count = 0
        if self._state == "half-open":
            self._state = "closed"
            logger.info("Circuit breaker closed after successful call")

    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = "open"
            logger.warning(
                "Circuit breaker opened",
                failures=self._failure_count,
                threshold=self.failure_threshold,
            )


async def retry_with_circuit_breaker(
    func: Callable[..., Awaitable[T]],
    *args,
    policy: RetryPolicy = DEFAULT_RETRY,
    circuit_breaker: CircuitBreaker | None = None,
    fallback: Callable[..., Awaitable[T]] | None = None,
    **kwargs,
) -> T:
    """
    Executa função com retry e circuit breaker opcional.

    Se circuit breaker abrir e houver fallback, executa o fallback.
    """
    attempt = 0
    last_exception = None

    while attempt < policy.max_attempts:
        attempt += 1

        try:
            if circuit_breaker:
                return await circuit_breaker.call(func, *args, **kwargs)
            else:
                return await func(*args, **kwargs)
        except CircuitBreakerOpenError:
            if fallback:
                logger.warning("Circuit breaker open, executing fallback")
                return await fallback(*args, **kwargs)
            raise
        except policy.retryable_exceptions as e:
            last_exception = e
            if attempt < policy.max_attempts:
                delay = min(
                    policy.base_delay_ms * (policy.exponential_base ** (attempt - 1)),
                    policy.max_delay_ms,
                )
                if policy.jitter:
                    delay = delay * (0.5 + random.random())  # 50-150%
                logger.warning(
                    "Retry attempt",
                    attempt=attempt,
                    max_attempts=policy.max_attempts,
                    delay_ms=delay,
                    error=str(e),
                )
                await asyncio.sleep(delay / 1000)
            else:
                logger.error("Max retry attempts reached", error=str(last_exception))
                raise

    raise last_exception


class AsyncRetryContext:
    """Context manager para retry manual com logging."""

    def __init__(
        self,
        operation_name: str,
        policy: RetryPolicy = DEFAULT_RETRY,
    ):
        self.operation_name = operation_name
        self.policy = policy
        self.attempt = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    async def execute(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        while True:
            self.attempt += 1
            try:
                return await func(*args, **kwargs)
            except self.policy.retryable_exceptions as e:
                if self.attempt >= self.policy.max_attempts:
                    logger.error(
                        f"{self.operation_name} failed after {self.attempt} attempts",
                        error=str(e),
                    )
                    raise
                delay = min(
                    self.policy.base_delay_ms
                    * (self.policy.exponential_base ** (self.attempt - 1)),
                    self.policy.max_delay_ms,
                )
                if self.policy.jitter:
                    delay = delay * (0.5 + random.random())
                logger.warning(
                    f"{self.operation_name} retry {self.attempt}/{self.policy.max_attempts}",
                    delay_ms=delay,
                    error=str(e),
                )
                await asyncio.sleep(delay / 1000)
