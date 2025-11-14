import logging

import pytest

from wanaspects.config import Config
from wanaspects.filters.redaction import RedactionFilter
from wanaspects.formatters.unicode_safe import UnicodeSafeFormatter
from wanaspects.telemetry import init_telemetry


@pytest.fixture(autouse=True)
def cleanup_redaction_filters():
    root = logging.getLogger()
    try:
        yield
    finally:
        for existing in list(root.filters):
            if isinstance(existing, RedactionFilter):
                root.removeFilter(existing)


@pytest.fixture()
def cleanup_handlers():
    root = logging.getLogger()
    old_handlers = list(root.handlers)
    try:
        yield root
    finally:
        for handler in list(root.handlers):
            if handler not in old_handlers:
                root.removeHandler(handler)
                handler.close()


def test_init_telemetry_installs_redaction_filter(monkeypatch):
    def fake_load_config() -> Config:
        return Config(enable_redaction=True, redact_keys=("session_id",))

    monkeypatch.setattr("wanaspects.telemetry.load_config", fake_load_config)

    init_telemetry()

    filters = [f for f in logging.getLogger().filters if isinstance(f, RedactionFilter)]
    assert len(filters) == 1

    record = logging.LogRecord("test", logging.INFO, __file__, 1, "session_id=abc", (), None)
    filters[0].filter(record)
    assert record.msg == "session_id=<REDACTED>"


def test_init_telemetry_removes_filter_when_disabled(monkeypatch):
    root = logging.getLogger()
    root.addFilter(RedactionFilter({"keep"}))

    def fake_load_config() -> Config:
        return Config(enable_redaction=False)

    monkeypatch.setattr("wanaspects.telemetry.load_config", fake_load_config)

    init_telemetry()

    assert not any(isinstance(f, RedactionFilter) for f in root.filters)


def test_init_telemetry_applies_unicode_formatter(monkeypatch, cleanup_handlers):
    root = cleanup_handlers

    class DummyStream:
        def __init__(self) -> None:
            self.encoding = "cp1252"

        def write(self, data: str) -> int:  # pragma: no cover - simple stub
            return len(data)

        def flush(self) -> None:  # pragma: no cover - simple stub
            pass

    handler = logging.StreamHandler(DummyStream())
    root.addHandler(handler)

    def fake_load_config() -> Config:
        return Config(
            enable_redaction=False,
            unicode_safe=True,
            strip_emoji=True,
        )

    monkeypatch.setattr("wanaspects.telemetry.load_config", fake_load_config)

    init_telemetry()

    assert isinstance(handler.formatter, UnicodeSafeFormatter)
    assert handler.formatter.encoding == "cp1252"


def test_init_telemetry_configures_rotation(monkeypatch, tmp_path, cleanup_handlers):
    root = cleanup_handlers

    log_path = tmp_path / "app.log"

    def fake_load_config() -> Config:
        return Config(
            enable_redaction=False,
            log_rotation_enabled=True,
            log_rotation_path=str(log_path),
            log_rotation_max_bytes=512,
        )

    monkeypatch.setattr("wanaspects.telemetry.load_config", fake_load_config)

    init_telemetry()

    rotation_handlers = [
        handler
        for handler in root.handlers
        if getattr(handler, "baseFilename", None) == str(log_path)
    ]
    assert rotation_handlers, "rotation handler not attached"
