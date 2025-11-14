from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from .core.aspect import Aspect
from .core.context import AdviceContext


class OptimizedAspectManager:
    """Performance-optimized AspectManager with fast paths.

    Optimizations:
    - Fast path for 0 aspects (direct call)
    - Fast path for 1 aspect (avoid loops and reduce)
    - __slots__ for memory efficiency
    - Local variable caching
    - Tuple instead of list (immutable, faster)
    - Proper closure capture for around chain
    - Optimized exception handling (separate success/error paths)
    """

    __slots__ = ("_aspects", "_count", "_single_aspect")

    def __init__(self, aspects: Iterable[Aspect] | None = None) -> None:
        # Use tuple for faster iteration and immutability
        self._aspects: tuple[Aspect, ...] = tuple(aspects or [])
        self._count: int = len(self._aspects)
        # Cache single aspect for fast path
        self._single_aspect: Aspect | None = self._aspects[0] if self._count == 1 else None

    def run(self, ctx: AdviceContext, call: Callable[[], Any]) -> Any:
        # Ultra-fast path: no aspects
        if self._count == 0:
            return call()

        # Fast path: single aspect (avoid all overhead)
        if self._single_aspect is not None:
            a = self._single_aspect
            a.before(ctx)
            try:
                result = a.around(ctx, call)
                a.after(ctx, result, None)
                return result
            except Exception as exc:
                a.after(ctx, None, exc)
                raise

        # Optimized multi-aspect path
        aspects = self._aspects  # Local cache for faster access

        # Execute all before hooks
        for a in aspects:
            a.before(ctx)

        # Build around chain with proper closure capture
        wrapped_call = call
        for aspect in reversed(aspects):
            # Build a wrapped call using a nested function instead of a lambda
            def _make_wrapped(a: Aspect, inner_call: Callable[[], Any]) -> Callable[[], Any]:
                def _inner() -> Any:
                    return a.around(ctx, lambda: inner_call())

                return _inner

            wrapped_call = _make_wrapped(aspect, wrapped_call)

        # Optimized exception handling (separate success/error paths)
        try:
            result = wrapped_call()
            # Success path: avoid storing error variable
            for a in aspects:
                a.after(ctx, result, None)
            return result
        except Exception as exc:
            # Error path: call after with exception
            for a in aspects:
                a.after(ctx, None, exc)
            raise
