import pytest

from wanaspects.aspects import ChainContractError
from wanaspects.aspects.contract import ContractAspect
from wanaspects.core.context import AdviceContext
from wanaspects.guards import materialize
from wanaspects.manager import AspectManager


def test_materialize_blocked_without_boundary() -> None:
    m = AspectManager([ContractAspect()])
    ctx = AdviceContext(step_name="s", container_shape="single", boundary="none")

    def call() -> None:
        with pytest.raises(ChainContractError):
            materialize(lambda: "collected")

    m.run(ctx, call)


def test_materialize_allowed_at_boundary() -> None:
    m = AspectManager([ContractAspect()])
    ctx = AdviceContext(step_name="s", container_shape="single", boundary="io")

    def call() -> None:
        assert materialize(lambda: "ok") == "ok"

    m.run(ctx, call)
