"""Verify the metrics aspect actually exports through a real MeterProvider.

These guard the integration that ``telemetry._try_init_metrics`` installs a
global MeterProvider so the aspect's instruments leave the no-op default and
become scrapeable by Prometheus.
"""

from __future__ import annotations

import importlib

import pytest

from wanaspects.aspects.metrics import MetricsAspect
from wanaspects.core.context import AdviceContext
from wanaspects.manager import AspectManager

prometheus_client = pytest.importorskip("prometheus_client")
pytest.importorskip("opentelemetry.exporter.prometheus")


def test_metrics_exported_to_prometheus_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WANCHAIN_ASPECTS_ENABLED", "true")
    monkeypatch.setenv("WANCHAIN_METRICS_ENABLED", "true")
    monkeypatch.setenv("WANCHAIN_METRICS_EXPORTER", "prometheus")
    monkeypatch.delenv("WANCHAIN_METRICS_PORT", raising=False)

    # Reset the module guard so the provider installs within this test process.
    telemetry = importlib.import_module("wanaspects.telemetry")
    monkeypatch.setitem(telemetry._METRICS_STATE, "initialized", False)

    telemetry.init_telemetry()

    # Instruments bind to the active provider at construction; build after init.
    manager = AspectManager([MetricsAspect()])
    ctx = AdviceContext(step_name="export_step", container_shape="single", boundary="none")
    assert manager.run(ctx, lambda: "ok") == "ok"

    scrape = prometheus_client.generate_latest(prometheus_client.REGISTRY).decode("utf-8")
    assert "wanchain_steps" in scrape
    assert "export_step" in scrape
