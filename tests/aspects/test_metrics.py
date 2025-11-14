import pytest

from wanaspects.aspects.metrics import MetricsAspect
from wanaspects.core.context import AdviceContext
from wanaspects.manager import AspectManager


def test_metrics_aspect_counts_success() -> None:
    aspect = MetricsAspect()
    ctx = AdviceContext(step_name="s", container_shape="single", boundary="none")
    manager = AspectManager([aspect])

    assert manager.run(ctx, lambda: "ok") == "ok"

    key = ("s", "single", "none", "ok")
    assert aspect._steps_total[key] == 1  # type: ignore[attr-defined]


def test_metrics_aspect_counts_errors() -> None:
    aspect = MetricsAspect()
    ctx = AdviceContext(step_name="s", container_shape="single", boundary="none")
    manager = AspectManager([aspect])

    def failing() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        manager.run(ctx, failing)

    error_key = ("s", "single", "none", "ValueError")
    assert aspect._step_errors_total[error_key] == 1  # type: ignore[attr-defined]
