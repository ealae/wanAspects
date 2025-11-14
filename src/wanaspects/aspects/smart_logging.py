from __future__ import annotations

from typing import Any, Literal

from ..core.context import AdviceContext
from .logging import LoggingAspect

LoggingTier = Literal["development", "production", "debug"]


class SmartLoggingAspect(LoggingAspect):
    """Intelligent logging aspect that adapts based on environment tier.

    Logging strategy by tier:
    - development: Full verbose logging (all before/after events)
    - production: Smart logging (errors + boundaries only, skip noisy internal calls)
    - debug: Trace-correlated logging (log when trace_id present, useful for debugging)

    This reduces logging overhead in production while maintaining comprehensive
    error tracking and boundary observability.
    """

    def __init__(self, tier: LoggingTier = "production") -> None:
        super().__init__()
        self.tier = tier

    def _should_log_before(self, ctx: AdviceContext) -> bool:
        """Determine if step_start should be logged."""
        if self.tier == "development":
            return True  # Full logging in dev

        # In production/debug, skip verbose step_start (too noisy)
        # We still get full visibility from step_end and OTel spans
        return False

    def _should_log_after(
        self, ctx: AdviceContext, error: Exception | None
    ) -> bool:
        """Determine if step_end should be logged."""
        # ALWAYS log errors (100% error coverage)
        if error is not None:
            return True

        if self.tier == "development":
            return True  # Full logging in dev

        if self.tier == "production":
            # In production, only log boundary events (service entry/exit)
            # This gives visibility into service calls without noise from
            # millions of internal successful function calls
            return ctx.boundary in ("entry", "exit", "geo", "io")

        if self.tier == "debug":
            # In debug mode, log if we're in an active trace
            # This correlates logs with OTel sampled traces
            return ctx.trace_id is not None

        return False

    def before(self, ctx: AdviceContext) -> None:
        """Log step_start only if appropriate for tier."""
        if self._should_log_before(ctx):
            super().before(ctx)

    def after(
        self, ctx: AdviceContext, result: Any, error: Exception | None
    ) -> None:
        """Log step_end based on tier and context."""
        if self._should_log_after(ctx, error):
            super().after(ctx, result, error)
