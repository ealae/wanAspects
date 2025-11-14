import pytest

from wanaspects.aspects import ChainContractError
from wanaspects.aspects.contract import ContractAspect
from wanaspects.core.context import AdviceContext


def test_unknown_boundary_fails_fast() -> None:
    a = ContractAspect()
    ctx = AdviceContext(step_name="s", container_shape="single", boundary="bad")  # type: ignore[arg-type]
    with pytest.raises(ChainContractError):
        a.before(ctx)
