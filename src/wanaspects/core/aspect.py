from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeVar

from .context import AdviceContext

T = TypeVar("T")


class Aspect(Protocol):
    def before(self, ctx: AdviceContext) -> None:  # pragma: no cover - interface only
        ...

    def around(self, ctx: AdviceContext, call: Callable[[], T]) -> T:  # pragma: no cover
        ...

    def after(
        self, ctx: AdviceContext, result: Any, error: Exception | None
    ) -> None:  # pragma: no cover
        ...
