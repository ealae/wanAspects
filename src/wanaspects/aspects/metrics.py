from __future__ import annotations

import contextvars
import time
from collections.abc import Callable
from typing import Any

from ..core.aspect import Aspect
from ..core.context import AdviceContext

_DURATION_SECONDS: contextvars.ContextVar[float | None] = contextvars.ContextVar(
    "wanaspects_metrics_duration_seconds", default=None
)


class MetricsAspect(Aspect):
    def __init__(self) -> None:
        self._steps_total: dict[tuple[str, str, str, str], int] = {}
        self._step_errors_total: dict[tuple[str, str, str, str], int] = {}
        self._counter_steps: Any | None = None
        self._hist_duration: Any | None = None
        self._counter_errors: Any | None = None
        # Optional OpenTelemetry metrics
        self._otel = False
        # optional OpenTelemetry metrics
        try:  # pragma: no cover - environment dependent
            from opentelemetry import metrics as _metrics  # noqa: PLC0415

            meter = _metrics.get_meter("wanaspects")
            # Keep attribute names low-cardinality as per contract
            self._counter_steps = meter.create_counter("wanchain_steps_total")
            self._hist_duration = meter.create_histogram("wanchain_step_duration_seconds")
            self._counter_errors = meter.create_counter("wanchain_step_errors_total")
            self._otel = True
        except Exception:
            self._otel = False

    def before(self, ctx: AdviceContext) -> None:
        return None

    def around(self, ctx: AdviceContext, call: Callable[[], Any]) -> Any:
        start = time.perf_counter()
        try:
            return call()
        finally:
            duration = time.perf_counter() - start
            _DURATION_SECONDS.set(duration)

    def after(self, ctx: AdviceContext, result: Any, error: Exception | None) -> None:
        status = "error" if error else "ok"
        duration = _DURATION_SECONDS.get(None)
        _DURATION_SECONDS.set(None)
        key = (ctx.step_name, ctx.container_shape, ctx.boundary, status)
        self._steps_total[key] = self._steps_total.get(key, 0) + 1
        if error is not None:
            err_key = (
                ctx.step_name,
                ctx.container_shape,
                ctx.boundary,
                error.__class__.__name__,
            )
            self._step_errors_total[err_key] = self._step_errors_total.get(err_key, 0) + 1
        if self._otel and self._counter_steps is not None and self._hist_duration is not None:
            try:
                attrs = {
                    "step": ctx.step_name,
                    "shape": ctx.container_shape,
                    "boundary": ctx.boundary,
                    "status": status,
                }
                self._counter_steps.add(1, attributes=attrs)
                if duration is not None:
                    self._hist_duration.record(duration, attributes=attrs)
                if error is not None and self._counter_errors is not None:
                    err_attrs = {
                        "step": ctx.step_name,
                        "shape": ctx.container_shape,
                        "boundary": ctx.boundary,
                        "error_kind": error.__class__.__name__,
                    }
                    self._counter_errors.add(1, attributes=err_attrs)
            except Exception:
                pass
