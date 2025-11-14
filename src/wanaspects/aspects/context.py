from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..context import reset_current_context, set_current_context
from ..core.aspect import Aspect
from ..core.context import AdviceContext


class ContextPropagationAspect(Aspect):
    """Expose the current AdviceContext via contextvars for downstream helpers."""

    def before(self, ctx: AdviceContext) -> None:
        set_current_context(ctx)

    def around(self, ctx: AdviceContext, call: Callable[[], Any]) -> Any:
        return call()

    def after(self, ctx: AdviceContext, result: Any, error: Exception | None) -> None:
        reset_current_context()
