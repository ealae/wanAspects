from __future__ import annotations

import contextvars
import logging
import time
from collections.abc import Callable
from typing import Any

from ..core.aspect import Aspect
from ..core.context import AdviceContext

# optional structlog integration
try:  # pragma: no cover - import environment dependent
    import structlog as _structlog
except Exception:  # pragma: no cover
    _structlog = None

_DURATION_MS: contextvars.ContextVar[float | None] = contextvars.ContextVar(
    "wanaspects_logging_duration_ms", default=None
)


class LoggingAspect(Aspect):
    def __init__(self) -> None:
        self._logger = logging.getLogger("wanaspects")

    @staticmethod
    def _sanitize_for_stdlib(fields: dict[str, Any]) -> dict[str, Any]:
        return {key.replace(".", "_"): value for key, value in fields.items()}

    def _event_fields(
        self,
        ctx: AdviceContext,
        status: str | None = None,
        duration_ms: float | None = None,
        error: Exception | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "step": ctx.step_name,
            "shape": ctx.container_shape,
            "boundary": ctx.boundary,
        }
        if ctx.run_id is not None:
            data["run_id"] = ctx.run_id
        if ctx.tenant is not None:
            data["tenant"] = ctx.tenant
        if ctx.trace_id is not None:
            data["trace_id"] = ctx.trace_id
        if ctx.span_id is not None:
            data["span_id"] = ctx.span_id
        if ctx.config_hash is not None:
            data["config_hash"] = ctx.config_hash
        if ctx.package_versions:
            data["versions"] = ctx.package_versions
        if status is not None:
            data["status"] = status
        if duration_ms is not None:
            data["duration_ms"] = duration_ms
        if error is not None:
            data["error.kind"] = error.__class__.__name__
            data["error.msg"] = str(error)
        return data

    def before(self, ctx: AdviceContext) -> None:
        fields = self._event_fields(ctx)
        if _structlog is not None:
            _structlog.get_logger("wanaspects").debug("step_start", **fields)
        # Always emit stdlib logging for capture without extra setup
        self._logger.debug("step_start", extra=self._sanitize_for_stdlib(fields))

    def around(self, ctx: AdviceContext, call: Callable[[], Any]) -> Any:
        start = time.perf_counter()
        try:
            return call()
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            _DURATION_MS.set(elapsed_ms)

    def after(self, ctx: AdviceContext, result: Any, error: Exception | None) -> None:
        status = "error" if error else "ok"
        duration_ms = _DURATION_MS.get(None)
        _DURATION_MS.set(None)
        fields = self._event_fields(ctx, status, duration_ms, error)
        if _structlog is not None:
            logger = _structlog.get_logger("wanaspects")
            if error:
                logger.error("step_end", **fields)
            else:
                logger.info("step_end", **fields)
        level = logging.ERROR if error else logging.INFO
        self._logger.log(level, "step_end", extra=self._sanitize_for_stdlib(fields))
