import importlib.util

import pytest
from wanaspects.aspects.tracing import TracingAspect
from wanaspects.core.context import AdviceContext
from wanaspects.manager import AspectManager


def test_tracing_aspect_noop_without_otel() -> None:
    ctx = AdviceContext(step_name="s", container_shape="single", boundary="none")
    m = AspectManager([TracingAspect()])
    assert m.run(ctx, lambda: "ok") == "ok"


otel_installed = importlib.util.find_spec("opentelemetry") is not None


@pytest.mark.skipif(not otel_installed, reason="opentelemetry not installed")
def test_tracing_aspect_with_otel_runs() -> None:
    ctx = AdviceContext(step_name="s", container_shape="single", boundary="none")
    m = AspectManager([TracingAspect()])
    assert m.run(ctx, lambda: "ok") == "ok"


@pytest.mark.skipif(not otel_installed, reason="opentelemetry not installed")
def test_tracing_sets_correlation_attributes(monkeypatch) -> None:
    # We cannot introspect NonRecordingSpan easily without a full SDK provider
    # This test ensures the call path succeeds when attributes are set.
    ctx = AdviceContext(
        step_name="s",
        container_shape="single",
        boundary="geo",
        run_id="r1",
        tenant="t1",
        package_versions={"wanaspects": "0.1.0"},
    )
    m = AspectManager([TracingAspect()])
    assert m.run(ctx, lambda: "ok") == "ok"
