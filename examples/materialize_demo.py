from __future__ import annotations

from wanaspects import AspectManager
from wanaspects.aspects import ContractAspect
from wanaspects.core.context import AdviceContext
from wanaspects.guards import ContractViolation, materialize


def run_no_boundary() -> None:
    print("-- no boundary (should fail) --")
    m = AspectManager([ContractAspect()])
    ctx = AdviceContext(step_name="no_boundary", container_shape="single", boundary="none")

    def step() -> None:
        # Not allowed: raises ContractViolation
        materialize(lambda: "collect")

    try:
        m.run(ctx, step)
    except ContractViolation as exc:
        print("raised:", exc)


def run_with_io_boundary() -> None:
    print("-- io boundary (should succeed) --")
    m = AspectManager([ContractAspect()])
    ctx = AdviceContext(step_name="io_boundary", container_shape="single", boundary="io")

    def step() -> str:
        return materialize(lambda: "ok")

    print("result:", m.run(ctx, step))


if __name__ == "__main__":
    run_no_boundary()
    run_with_io_boundary()
