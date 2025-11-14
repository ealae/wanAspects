from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..context import reset_current_context, set_current_context
from ..core.aspect import Aspect
from ..core.context import AdviceContext


class ConditionalContextPropagationAspect(Aspect):
    """Context propagation aspect that only propagates for boundary calls.

    In high-performance scenarios, context propagation adds overhead (44x) for
    every call. However, context is primarily needed at service boundaries for
    distributed tracing correlation, not for every internal function call.

    This aspect only propagates context when:
    - boundary is not "none" (i.e., entry, exit, geo, io)
    - OR when explicitly needed (trace_id present)

    This reduces overhead significantly while maintaining context where it matters.
    """

    def __init__(self, propagate_all: bool = False) -> None:
        """Initialize conditional context propagation.

        Args:
            propagate_all: If True, always propagate (like regular ContextPropagationAspect).
                          If False (default), only propagate for boundary calls.
        """
        self.propagate_all = propagate_all

    def _should_propagate(self, ctx: AdviceContext) -> bool:
        """Determine if context should be propagated for this call."""
        if self.propagate_all:
            return True

        # Propagate for boundary calls (service entry/exit)
        if ctx.boundary != "none":
            return True

        # Propagate if we're in an active trace (need correlation)
        if ctx.trace_id is not None:
            return True

        # Skip propagation for internal calls without tracing
        return False

    def before(self, ctx: AdviceContext) -> None:
        if self._should_propagate(ctx):
            set_current_context(ctx)

    def around(self, ctx: AdviceContext, call: Callable[[], Any]) -> Any:
        return call()

    def after(self, ctx: AdviceContext, result: Any, error: Exception | None) -> None:
        if self._should_propagate(ctx):
            reset_current_context()
