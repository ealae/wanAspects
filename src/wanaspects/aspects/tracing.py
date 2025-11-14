from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..core.aspect import Aspect
from ..core.context import AdviceContext

# optional OpenTelemetry integration
_trace: Any | None
_OtelStatus: Any | None
_OtelStatusCode: Any | None
try:  # pragma: no cover - import environment dependent
    from opentelemetry import trace as _trace
    from opentelemetry.trace import Status as _OtelStatus
    from opentelemetry.trace import StatusCode as _OtelStatusCode
except Exception:  # pragma: no cover
    _trace = None
    _OtelStatus = None
    _OtelStatusCode = None


class TracingAspect(Aspect):
    def before(self, ctx: AdviceContext) -> None:
        return None

    def around(self, ctx: AdviceContext, call: Callable[[], Any]) -> Any:
        if _trace is None:
            return call()
        tracer = _trace.get_tracer("wanaspects")
        with tracer.start_as_current_span(ctx.step_name) as span:
            try:
                # attributes per naming spec
                if getattr(span, "set_attribute", None):  # NonRecordingSpan safe guard
                    span.set_attribute("wanchain.step.name", ctx.step_name)
                    span.set_attribute("wanchain.container.shape", ctx.container_shape)
                    span.set_attribute("wanchain.boundary", ctx.boundary)
                    if ctx.run_id is not None:
                        span.set_attribute("wanchain.run.id", ctx.run_id)
                    if ctx.tenant is not None:
                        span.set_attribute("wanchain.tenant", ctx.tenant)
                    if ctx.package_versions:
                        # Store as a string to keep attribute scalar
                        span.set_attribute("wanchain.versions", str(ctx.package_versions))
                return call()
            except Exception as exc:  # noqa: BLE001
                if (
                    getattr(span, "record_exception", None)
                    and _OtelStatus is not None
                    and _OtelStatusCode is not None
                ):
                    span.record_exception(exc)
                    span.set_status(_OtelStatus(_OtelStatusCode.ERROR))
                raise

    def after(self, ctx: AdviceContext, result: Any, error: Exception | None) -> None:
        return None
