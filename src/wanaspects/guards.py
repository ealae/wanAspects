from __future__ import annotations

import contextvars
from collections.abc import Callable
from typing import Any


class ChainContractError(RuntimeError):
    pass


# Materialization permission follows the current step boundary.
_ALLOW_MATERIALIZE: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "wanaspects_allow_materialize", default=False
)


def materialize(fn: Callable[[], Any]) -> Any:
    """Guarded materialization helper.

    Raises ContractViolation when called inside a step without a boundary.
    Callers at a boundary step (e.g., boundary != 'none') may materialize safely.
    """

    if not _ALLOW_MATERIALIZE.get():
        raise ChainContractError(
            "Materialization not allowed inside chain. Mark the step with a boundary (geo|io) "
            "or move collection outside the chain."
        )
    return fn()


def _set_allow_materialize(value: bool) -> contextvars.Token[bool]:
    return _ALLOW_MATERIALIZE.set(value)


def _reset_allow_materialize(token: contextvars.Token[bool]) -> None:
    _ALLOW_MATERIALIZE.reset(token)


# Backward compatibility: retain old name referenced in early drafts.
ContractViolation = ChainContractError

__all__ = ["ChainContractError", "ContractViolation", "materialize"]
