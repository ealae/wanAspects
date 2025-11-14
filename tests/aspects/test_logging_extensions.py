from __future__ import annotations

import logging
from typing import Any

import pytest
from wanaspects.aspects import logging_extensions as domain_logging


class CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - tested indirectly
        self.records.append(record)


@pytest.fixture()
def capture_logger() -> LoggerCapture:
    logger = logging.getLogger("wanaspects.tests.domain")
    handler = CaptureHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield logger, handler
    finally:
        logger.removeHandler(handler)


def latest(handler: CaptureHandler) -> logging.LogRecord:
    assert handler.records, "No records captured"
    return handler.records[-1]


LoggerCapture = tuple[logging.Logger, CaptureHandler]
HTTP_UNAVAILABLE = 503


def test_log_db_query_success(capture_logger: LoggerCapture) -> None:
    logger, handler = capture_logger

    domain_logging.log_db_query(
        logger,
        "SELECT * FROM user WHERE id=%(id)s",
        parameters={"id": 1},
        duration_ms=12.5,
        row_count=1,
    )

    record = latest(handler)
    assert record.msg == "db.query"
    assert record.levelno == logging.INFO
    assert record.db["statement"] == "SELECT * FROM user WHERE id=%(id)s"
    assert record.db["parameters"] == {"id": 1}
    assert record.db["duration_ms"] == pytest.approx(12.5)
    assert record.db["row_count"] == 1
    assert record.db["success"] is True


def test_log_db_query_failure_records_error(capture_logger: LoggerCapture) -> None:
    logger, handler = capture_logger
    err = RuntimeError("boom")

    domain_logging.log_db_query(
        logger,
        "UPDATE user SET email=%s",
        parameters=("user@example.com",),
        success=False,
        error=err,
    )

    record = latest(handler)
    assert record.levelno == logging.ERROR
    assert record.db["success"] is False
    assert record.db["error_kind"] == "RuntimeError"
    assert record.db["error_message"] == "boom"


def test_log_cache_operation_hit(capture_logger: LoggerCapture) -> None:
    logger, handler = capture_logger

    domain_logging.log_cache_operation(
        logger,
        operation="get",
        key="profile:1",
        namespace="redis",
        hit=True,
        duration_ms=4.2,
    )

    record = latest(handler)
    assert record.msg == "cache.operation"
    assert record.cache_event == {
        "operation": "get",
        "key": "profile:1",
        "namespace": "redis",
        "hit": True,
        "duration_ms": pytest.approx(4.2),
        "success": True,
    }


def test_log_api_call_failure_defaults_status(capture_logger: LoggerCapture) -> None:
    logger, handler = capture_logger

    domain_logging.log_api_call(
        logger,
        method="GET",
        url="https://example.test/users",
        status_code=503,
        duration_ms=300.0,
        request_id="req-123",
        error=TimeoutError("deadline exceeded"),
    )

    record = latest(handler)
    assert record.msg == "api.call"
    assert record.levelno == logging.ERROR
    payload: dict[str, Any] = record.api_call
    assert payload["method"] == "GET"
    assert payload["url"] == "https://example.test/users"
    assert payload["status_code"] == HTTP_UNAVAILABLE
    assert payload["request_id"] == "req-123"
    assert payload["duration_ms"] == pytest.approx(300.0)
    assert payload["success"] is False
    assert payload["error_kind"] == "TimeoutError"
    assert payload["error_message"] == "deadline exceeded"
