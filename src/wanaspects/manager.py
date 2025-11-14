from __future__ import annotations

from collections.abc import Callable, Iterable
from functools import reduce
from typing import Any

from .core.aspect import Aspect
from .core.context import AdviceContext


class AspectManager:
    def __init__(self, aspects: Iterable[Aspect] | None = None) -> None:
        self._aspects: list[Aspect] = list(aspects or [])

    def run(self, ctx: AdviceContext, call: Callable[[], Any]) -> Any:
        for a in self._aspects:
            a.before(ctx)

        def around_chain(inner: Callable[[], Any], aspect: Aspect) -> Callable[[], Any]:
            return lambda: aspect.around(ctx, inner)

        wrapped_call = reduce(around_chain, reversed(self._aspects), call)

        error: Exception | None = None
        result: Any = None
        try:
            result = wrapped_call()
            return result
        except Exception as exc:  # noqa: BLE001 - bubble after after()
            error = exc
            raise
        finally:
            for a in self._aspects:
                a.after(ctx, result, error)
