from __future__ import annotations

"""Testes unitários para laya_ultrafast."""

import pytest

from laya_ultrafast.core.exceptions import (
    NON_RETRYABLE_EXCEPTIONS,
    RETRYABLE_EXCEPTIONS,
    is_non_retryable,
    is_retryable,
)
from laya_ultrafast.utils.dom import (
    ElementSnapshot,
    build_element_summary,
    extract_interactive_elements,
    filter_visible_elements,
)
from laya_ultrafast.utils.geometry import BoundingBox, Viewport, compute_element_visibility


class TestGeometry:
    """Testes para utilitários geométricos."""

    def test_bounding_box_creation(self):
        box = BoundingBox(x=10, y=20, width=100, height=50)
        assert box.left == 10
        assert box.top == 20
        assert box.right == 110
        assert box.bottom == 70
        assert box.center_x == 60
        assert box.center_y == 45
        assert box.area == 5000

    def test_bounding_box_contains_point(self):
        box = BoundingBox(x=0, y=0, width=100, height=100)
        assert box.contains_point(50, 50)
        assert box.contains_point(0, 0)
        assert box.contains_point(100, 100)
        assert not box.contains_point(-1, 50)
        assert not box.contains_point(101, 50)

    def test_bounding_box_intersection(self):
        box1 = BoundingBox(x=0, y=0, width=100, height=100)
        box2 = BoundingBox(x=50, y=50, width=100, height=100)
        inter = box1.intersection(box2)
        assert inter is not None
        assert inter.x == 50
        assert inter.y == 50
        assert inter.width == 50
        assert inter.height == 50

    def test_bounding_box_no_intersection(self):
        box1 = BoundingBox(x=0, y=0, width=50, height=50)
        box2 = BoundingBox(x=100, y=100, width=50, height=50)
        assert box1.intersection(box2) is None

    def test_bounding_box_iou(self):
        box1 = BoundingBox(x=0, y=0, width=100, height=100)
        box2 = BoundingBox(x=50, y=50, width=100, height=100)
        iou = box1.iou(box2)
        assert 0 < iou < 1
        assert abs(iou - (2500 / 17500)) < 0.001  # inter / union

    def test_viewport_is_in_viewport(self):
        vp = Viewport(width=800, height=600)
        box_inside = BoundingBox(x=100, y=100, width=200, height=200)
        box_outside = BoundingBox(x=900, y=100, width=200, height=200)
        assert vp.is_in_viewport(box_inside)
        assert not vp.is_in_viewport(box_outside)

    def test_compute_element_visibility(self):
        vp = Viewport(width=800, height=600, scroll_x=0, scroll_y=0)
        box_visible = BoundingBox(x=100, y=100, width=200, height=200)
        box_hidden = BoundingBox(x=900, y=100, width=200, height=200)
        
        visible, ratio = compute_element_visibility(box_visible, vp)
        assert visible
        assert ratio > 0.5
        
        visible, ratio = compute_element_visibility(box_hidden, vp)
        assert not visible
        assert ratio == 0.0


class TestDOM:
    """Testes para utilitários de DOM."""

    def create_snapshot(self, **overrides) -> ElementSnapshot:
        base = {
            "id": "test-1",
            "index": 0,
            "tag": "button",
            "role": "button",
            "label": "Clique aqui",
            "selector": "button#test",
            "bbox": {"x": 100, "y": 100, "width": 120, "height": 40},
            "attrs": {"type": "submit"},
            "state": {},
            "is_visible": True,
            "is_obstructed": False,
            "is_interactive": True,
            "is_editable": False,
        }
        base.update(overrides)
        return ElementSnapshot.from_dict(base)

    def test_element_snapshot_roundtrip(self):
        snap = self.create_snapshot()
        d = snap.to_dict()
        restored = ElementSnapshot.from_dict(d)
        assert restored.id == snap.id
        assert restored.label == snap.label
        assert restored.bbox == snap.bbox

    def test_extract_interactive_elements(self):
        snaps = [
            self.create_snapshot(is_interactive=True),
            self.create_snapshot(is_interactive=False, is_editable=True),
            self.create_snapshot(is_interactive=False, is_editable=False),
        ]
        interactive = extract_interactive_elements(snaps)
        assert len(interactive) == 2

    def test_filter_visible_elements(self):
        snaps = [
            self.create_snapshot(is_visible=True, is_obstructed=False),
            self.create_snapshot(is_visible=False, is_obstructed=False),
            self.create_snapshot(is_visible=True, is_obstructed=True),
        ]
        visible = filter_visible_elements(snaps)
        assert len(visible) == 1

    def test_build_element_summary(self):
        snaps = [
            self.create_snapshot(index=0, label="Botão 1"),
            self.create_snapshot(index=1, label="Botão 2"),
        ]
        summary = build_element_summary(snaps, max_elements=10)
        assert "[0] button: \"Botão 1\"" in summary
        assert "[1] button: \"Botão 2\"" in summary

    def test_build_element_summary_truncates(self):
        snaps = [self.create_snapshot(index=i, label=f"Btn {i}") for i in range(60)]
        summary = build_element_summary(snaps, max_elements=50)
        assert "... e mais 10 elementos" in summary


class TestExceptions:
    """Testes para hierarquia de exceções."""

    def test_retryable_exceptions(self):
        from laya_ultrafast.core.exceptions import BrowserConnectionError, ModelTimeoutError
        assert is_retryable(BrowserConnectionError("test"))
        assert is_retryable(ModelTimeoutError("test"))
        assert is_retryable(TimeoutError("test"))

    def test_non_retryable_exceptions(self):
        from laya_ultrafast.core.exceptions import ConfigurationError, ElementNotFoundError
        assert is_non_retryable(ConfigurationError("test"))
        assert is_non_retryable(ElementNotFoundError("test"))

    def test_retryable_list_matches(self):
        for exc in RETRYABLE_EXCEPTIONS:
            assert is_retryable(exc("test"))

    def test_non_retryable_list_matches(self):
        for exc in NON_RETRYABLE_EXCEPTIONS:
            assert is_non_retryable(exc("test"))


class TestRetry:
    """Testes para políticas de retry."""

    @pytest.mark.asyncio
    async def test_retry_policy_basic(self):
        from laya_ultrafast.utils.retry import FAST_RETRY
        
        assert FAST_RETRY.max_attempts == 2
        assert FAST_RETRY.base_delay_ms == 100

    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        from laya_ultrafast.utils.retry import CircuitBreaker, CircuitBreakerOpenError
        
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout_ms=100)
        
        async def fail():
            raise ValueError("fail")
        
        # Primeira falha
        with pytest.raises(ValueError):
            await cb.call(fail)
        assert cb.state == "closed"
        
        # Segunda falha - abre circuit
        with pytest.raises(ValueError):
            await cb.call(fail)
        assert cb.state == "open"
        
        # Terceira chamada - circuit open
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(fail)


class TestMetrics:
    """Testes para coletor de métricas."""

    def test_metrics_counter(self):
        from laya_ultrafast.utils.metrics import MetricsCollector
        
        m = MetricsCollector()
        m.increment("test.counter", 1)
        m.increment("test.counter", 2)
        assert m.get_counter("test.counter") == 3

    def test_metrics_gauge(self):
        from laya_ultrafast.utils.metrics import MetricsCollector
        
        m = MetricsCollector()
        m.gauge("test.gauge", 42.5)
        assert m.get_gauge("test.gauge") == 42.5

    def test_metrics_histogram_stats(self):
        from laya_ultrafast.utils.metrics import MetricsCollector
        
        m = MetricsCollector()
        for v in [10, 20, 30, 40, 50]:
            m.histogram("test.latency", v)
        
        stats = m.get_histogram_stats("test.latency")
        assert stats["count"] == 5
        assert stats["min"] == 10
        assert stats["max"] == 50
        assert stats["mean"] == 30


class TestActionExecutor:
    """Testes para executor de ações."""

    @pytest.mark.asyncio
    async def test_action_creation(self):
        from laya_ultrafast.core.action_executor import Action, ActionType
        
        click = Action.click("elem-1", "button#btn")
        assert click.type == ActionType.CLICK
        assert click.target_id == "elem-1"
        
        type_text = Action.type_text("elem-1", "input#txt", "hello")
        assert type_text.type == ActionType.TYPE_TEXT
        assert type_text.value == "hello"

    @pytest.mark.asyncio
    async def test_execution_result(self):
        from laya_ultrafast.core.action_executor import Action, ExecutionResult
        
        action = Action.click("elem-1", "button#btn")
        result = ExecutionResult(success=True, action=action, message="OK")
        assert result.success
        assert result.error is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])