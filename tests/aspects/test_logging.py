import logging

import pytest

from wanaspects.aspects.logging import LoggingAspect
from wanaspects.core.context import AdviceContext
from wanaspects.manager import AspectManager


class _Handler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - exercised
        self.records.append(record)


def _capture_logger() -> tuple[logging.Logger, _Handler]:
    logger = logging.getLogger("wanaspects")
    logger.setLevel(logging.DEBUG)
    handler = _Handler()
    logger.addHandler(handler)
    return logger, handler


def test_logging_aspect_emits_stdlib_records() -> None:
    logger, handler = _capture_logger()
    ctx = AdviceContext(
        step_name="s",
        container_shape="single",
        boundary="none",
        run_id="r1",
        tenant="t1",
        trace_id="trace-1",
        span_id="span-1",
        config_hash="cfg-1",
        package_versions={"wanaspects": "0.1.0"},
    )
    try:
        m = AspectManager([LoggingAspect()])
        assert m.run(ctx, lambda: "ok") == "ok"
    finally:
        logger.removeHandler(handler)

    records = handler.records
    assert any(r.msg == "step_start" for r in records)
    end = next(r for r in records if r.msg == "step_end")
    assert end.step == "s"  # type: ignore[attr-defined]
    assert end.shape == "single"  # type: ignore[attr-defined]
    assert end.boundary == "none"  # type: ignore[attr-defined]
    assert end.status == "ok"  # type: ignore[attr-defined]
    assert end.run_id == "r1"  # type: ignore[attr-defined]
    assert end.tenant == "t1"  # type: ignore[attr-defined]
    assert end.trace_id == "trace-1"  # type: ignore[attr-defined]
    assert end.span_id == "span-1"  # type: ignore[attr-defined]
    assert end.config_hash == "cfg-1"  # type: ignore[attr-defined]
    assert end.duration_ms > 0  # type: ignore[attr-defined]


def test_logging_aspect_captures_error_metadata() -> None:
    logger, handler = _capture_logger()
    ctx = AdviceContext(step_name="s", container_shape="single", boundary="none")

    def failing() -> None:
        raise ValueError("boom")

    try:
        m = AspectManager([LoggingAspect()])
        with pytest.raises(ValueError):
            m.run(ctx, failing)
    finally:
        logger.removeHandler(handler)

    end = next(r for r in handler.records if r.msg == "step_end")
    assert end.status == "error"  # type: ignore[attr-defined]
    assert end.error_kind == "ValueError"  # type: ignore[attr-defined]
    assert end.error_msg == "boom"  # type: ignore[attr-defined]
