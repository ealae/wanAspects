"""Domain-specific logging helpers for common operations."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

__all__ = ["log_db_query", "log_cache_operation", "log_api_call"]

HTTP_ERROR_THRESHOLD = 500


def _emit(  # noqa: PLR0913
    logger: logging.Logger,
    level: int,
    message: str,
    payload_key: str,
    payload: Mapping[str, Any],
    extra: Mapping[str, Any] | None,
) -> None:
    merged_extra: dict[str, Any] = {}
    if extra:
        merged_extra.update(extra)
    merged_extra[payload_key] = dict(payload)
    logger.log(level, message, extra=merged_extra)


def _error_fields(error: Exception | None) -> dict[str, Any]:
    if error is None:
        return {}
    return {
        "error_kind": error.__class__.__name__,
        "error_message": str(error),
    }


def log_db_query(  # noqa: PLR0913
    logger: logging.Logger,
    statement: str,
    *,
    parameters: Any | None = None,
    duration_ms: float | None = None,
    row_count: int | None = None,
    success: bool = True,
    error: Exception | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Log a database query with consistent structured fields."""

    payload: dict[str, Any] = {
        "statement": statement,
        "success": success and error is None,
    }
    if parameters is not None:
        payload["parameters"] = parameters
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
    if row_count is not None:
        payload["row_count"] = row_count
    if error is not None:
        payload["success"] = False
        payload.update(_error_fields(error))

    level = logging.INFO if payload["success"] else logging.ERROR
    _emit(logger, level, "db.query", "db", payload, extra)


def log_cache_operation(  # noqa: PLR0913
    logger: logging.Logger,
    *,
    operation: str,
    key: str,
    namespace: str | None = None,
    hit: bool | None = None,
    duration_ms: float | None = None,
    success: bool = True,
    error: Exception | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Log cache operations (get, set, invalidate, etc.)."""

    payload: dict[str, Any] = {
        "operation": operation,
        "key": key,
        "success": success and error is None,
    }
    if namespace is not None:
        payload["namespace"] = namespace
    if hit is not None:
        payload["hit"] = hit
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
    if error is not None:
        payload["success"] = False
        payload.update(_error_fields(error))

    level = logging.INFO if payload["success"] else logging.ERROR
    _emit(logger, level, "cache.operation", "cache_event", payload, extra)


def log_api_call(  # noqa: PLR0913
    logger: logging.Logger,
    *,
    method: str,
    url: str,
    status_code: int,
    duration_ms: float | None = None,
    request_id: str | None = None,
    success: bool | None = None,
    error: Exception | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Log outgoing or incoming API calls in a consistent schema."""

    computed_success = status_code < HTTP_ERROR_THRESHOLD
    payload_success = computed_success if success is None else success
    if error is not None:
        payload_success = False

    payload: dict[str, Any] = {
        "method": method,
        "url": url,
        "status_code": status_code,
        "success": payload_success,
    }
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
    if request_id is not None:
        payload["request_id"] = request_id
    if error is not None:
        payload.update(_error_fields(error))

    level = logging.INFO if payload_success else logging.ERROR
    _emit(logger, level, "api.call", "api_call", payload, extra)
