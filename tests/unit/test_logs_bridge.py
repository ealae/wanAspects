"""Verify the stdlib->OTLP logging bridge wiring.

``_try_init_logs`` should attach an OpenTelemetry ``LoggingHandler`` to the root
logger so stdlib records (and the logging aspect's step events) are forwarded to
the OTLP collector. Also guards the endpoint-path resolution helper.
"""

from __future__ import annotations

import importlib
import logging

import pytest

pytest.importorskip("opentelemetry.exporter.otlp.proto.http._log_exporter")
LoggingHandler = pytest.importorskip("opentelemetry.sdk._logs").LoggingHandler

telemetry = importlib.import_module("wanaspects.telemetry")


@pytest.mark.parametrize(
    "base,signal,expected",
    [
        ("http://127.0.0.1:4318", "logs", "http://127.0.0.1:4318/v1/logs"),
        ("http://127.0.0.1:4318/", "traces", "http://127.0.0.1:4318/v1/traces"),
        ("http://127.0.0.1:4318/v1", "logs", "http://127.0.0.1:4318/v1/logs"),
        ("http://host/v1/logs", "logs", "http://host/v1/logs"),
    ],
)
def test_otlp_endpoint_for(base: str, signal: str, expected: str) -> None:
    assert telemetry._otlp_endpoint_for(base, signal) == expected


def test_logs_bridge_attaches_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WANCHAIN_ASPECTS_ENABLED", "true")
    monkeypatch.setenv("WANCHAIN_LOGS_EXPORTER", "otlp")
    monkeypatch.setenv("WANCHAIN_OTLP_ENDPOINT", "http://127.0.0.1:4318")
    monkeypatch.setitem(telemetry._LOGS_STATE, "initialized", False)

    root = logging.getLogger()
    before = [h for h in root.handlers if isinstance(h, LoggingHandler)]

    telemetry.init_telemetry()

    try:
        after = [h for h in root.handlers if isinstance(h, LoggingHandler)]
        assert len(after) == len(before) + 1
        assert telemetry._LOGS_STATE["initialized"] is True
    finally:
        for handler in root.handlers[:]:
            if isinstance(handler, LoggingHandler) and handler not in before:
                root.removeHandler(handler)
