from __future__ import annotations

import contextvars

from .core.context import AdviceContext

_CURRENT_CONTEXT: contextvars.ContextVar[AdviceContext | None] = contextvars.ContextVar(
    "wanaspects_current_context", default=None
)
_CURRENT_TOKEN: contextvars.ContextVar[contextvars.Token[AdviceContext | None] | None] = (
    contextvars.ContextVar("wanaspects_current_context_token", default=None)
)


def set_current_context(ctx: AdviceContext) -> None:
    """Make ``ctx`` available to downstream helpers via contextvars."""

    token = _CURRENT_CONTEXT.set(ctx)
    _CURRENT_TOKEN.set(token)


def reset_current_context() -> None:
    """Reset the current AdviceContext when the step finishes."""

    token = _CURRENT_TOKEN.get()
    if token is not None:
        _CURRENT_CONTEXT.reset(token)
    _CURRENT_TOKEN.set(None)


def current_context() -> AdviceContext | None:
    """Return the AdviceContext for the active step, if any."""

    return _CURRENT_CONTEXT.get()


__all__ = ["current_context", "set_current_context", "reset_current_context"]
