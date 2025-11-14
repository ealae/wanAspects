from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..core.aspect import Aspect
from ..core.context import AdviceContext
from ..guards import ChainContractError, _reset_allow_materialize, _set_allow_materialize


class ContractAspect(Aspect):
    def before(self, ctx: AdviceContext) -> None:
        if ctx.boundary not in ("none", "geo", "io"):
            raise ChainContractError(f"Unknown boundary '{ctx.boundary}'. Valid: none, geo, io.")

    def around(self, ctx: AdviceContext, call: Callable[[], Any]) -> Any:
        # Enable materialization only for boundary steps
        token = _set_allow_materialize(ctx.boundary != "none")
        try:
            return call()
        finally:
            _reset_allow_materialize(token)

    def after(self, ctx: AdviceContext, result: Any, error: Exception | None) -> None:
        return None
