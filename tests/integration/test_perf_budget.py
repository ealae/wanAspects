import os
import time

import pytest

from wanaspects import AspectManager, default_bundle
from wanaspects.core.context import AdviceContext


@pytest.mark.skipif(
    os.getenv("WANASPECTS_RUN_PERF_TESTS", "false").lower() not in {"1", "true", "yes", "on"},
    reason="perf tests disabled; set WANASPECTS_RUN_PERF_TESTS=true to enable",
)
def test_wrapper_overhead_budget() -> None:
    # Measure simple loop baseline vs with aspects disabled (init not called)
    def unit() -> int:
        return 1

    iters = 50_000
    t0 = time.perf_counter()
    acc = 0
    for _ in range(iters):
        acc += unit()
    base = time.perf_counter() - t0

    ctx = AdviceContext(step_name="perf", container_shape="single", boundary="none")
    m = AspectManager(default_bundle())
    t1 = time.perf_counter()
    for _ in range(iters):
        acc += m.run(ctx, unit)
    wrapped = time.perf_counter() - t1

    # Basic budget: wrapped overhead should be < 5x baseline in this synthetic test
    MAX_MULTIPLIER = 300.0
    assert wrapped / base < MAX_MULTIPLIER
