from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from typing import Any

__all__ = ["Config", "load_config"]


@dataclass(frozen=True)
class Config:
    enabled: bool = False
    bundle: str = "default"  # default|dev|prod
    trace_sampling: float = 0.0
    otlp_endpoint: str | None = None
    console_spans: bool = False
    log_level: str = "INFO"
    log_json: bool = True
    boundary_allow: tuple[str, ...] = ("geo", "io")
    metrics_enabled: bool = False
    dev_peek_max_rows: int | None = None
    enable_redaction: bool = True
    redact_keys: tuple[str, ...] = ()
    unicode_safe: bool = True
    strip_emoji: bool | None = None
    force_utf8: bool = False
    log_rotation_enabled: bool = False
    log_rotation_path: str | None = None
    log_rotation_max_bytes: int = 10_485_760  # 10 MiB default
    log_rotation_backup_count: int = 5
    log_rotation_when: str | None = None
    log_rotation_interval: int = 1
    log_rotation_utc: bool = False


def _parse_bool(val: Any, default: bool = False) -> bool:
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in {"1", "true", "yes", "on"}


def _read_pyproject(path: str | None) -> dict[str, Any]:
    data: dict[str, Any] = {}
    try:
        file_path = path or "pyproject.toml"
        with open(file_path, "rb") as f:
            toml = tomllib.load(f)
        data = toml.get("tool", {}).get("wanchain", {}).get("aspects", {})
    except Exception:
        pass
    return data


def load_config(pyproject_path: str | None = None) -> Config:  # noqa: PLR0915
    """Load configuration from pyproject and environment; env wins."""

    base = _read_pyproject(pyproject_path)

    def g(key: str, default: Any = None) -> Any:
        return os.getenv(key, default)

    def _to_float(val: Any, default: float = 0.0) -> float:
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    def _to_int(val: Any) -> int | None:
        if val is None:
            return None
        if isinstance(val, int):
            return val
        s = str(val).strip()
        if not s:
            return None
        try:
            return int(s)
        except ValueError:
            return None

    # Compose with precedence (env > pyproject)
    enabled = _parse_bool(g("WANCHAIN_ASPECTS_ENABLED", base.get("enabled", False)))
    bundle = str(g("WANCHAIN_ASPECTS_BUNDLE", base.get("bundle", "default")))
    trace_sampling = _to_float(g("WANCHAIN_TRACE_SAMPLING", base.get("trace_sampling", 0.0)), 0.0)
    trace_sampling = max(0.0, min(1.0, trace_sampling))
    otlp_endpoint = g("WANCHAIN_OTLP_ENDPOINT", base.get("otlp_endpoint"))
    console_spans = _parse_bool(g("WANCHAIN_OTEL_CONSOLE", base.get("console_spans", False)))
    log_level = str(g("WANCHAIN_LOG_LEVEL", base.get("log_level", "INFO")))
    log_json = _parse_bool(g("WANCHAIN_LOG_JSON", base.get("log_json", True)), True)
    metrics_enabled = _parse_bool(g("WANCHAIN_METRICS_ENABLED", base.get("metrics_enabled", False)))
    dev_peek_max_rows = _to_int(g("WANCHAIN_DEV_PEEK_MAX_ROWS", base.get("dev_peek_max_rows")))
    boundary_allow_raw = g("WANCHAIN_BOUNDARY_ALLOW", base.get("boundary_allow", ["geo", "io"]))
    if isinstance(boundary_allow_raw, str):
        boundary_allow = tuple(x.strip() for x in boundary_allow_raw.split(",") if x.strip())
    else:
        boundary_allow = tuple(boundary_allow_raw)
    enable_redaction = _parse_bool(
        g("WANCHAIN_ENABLE_REDACTION", base.get("enable_redaction", True)),
        True,
    )
    redact_keys_raw = g("WANCHAIN_REDACT_KEYS", base.get("redact_keys", ()))
    if isinstance(redact_keys_raw, str):
        redact_keys = tuple(x.strip() for x in redact_keys_raw.split(",") if x.strip())
    else:
        redact_keys = tuple(str(x).strip() for x in redact_keys_raw if str(x).strip())

    def _parse_optional_bool(val: Any, default: bool | None = None) -> bool | None:
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        s = str(val).strip().lower()
        if s in {"", "auto", "default", "none"}:
            return None
        if s in {"1", "true", "yes", "on"}:
            return True
        if s in {"0", "false", "no", "off"}:
            return False
        return default

    unicode_safe = _parse_bool(g("WANCHAIN_UNICODE_SAFE", base.get("unicode_safe", True)), True)
    strip_emoji = _parse_optional_bool(g("WANCHAIN_STRIP_EMOJI", base.get("strip_emoji")))
    force_utf8 = _parse_bool(g("WANCHAIN_FORCE_UTF8", base.get("force_utf8", False)))
    log_rotation_enabled = _parse_bool(
        g("WANCHAIN_LOG_ROTATION_ENABLED", base.get("log_rotation_enabled", False)),
        False,
    )
    log_rotation_path = g("WANCHAIN_LOG_ROTATION_PATH", base.get("log_rotation_path"))
    max_bytes_raw = g(
        "WANCHAIN_LOG_ROTATION_MAX_BYTES",
        base.get("log_rotation_max_bytes", 10_485_760),
    )
    max_bytes = _to_int(max_bytes_raw) or 10_485_760
    backup_count_raw = g(
        "WANCHAIN_LOG_ROTATION_BACKUP_COUNT",
        base.get("log_rotation_backup_count", 5),
    )
    backup_count = _to_int(backup_count_raw) or 5
    log_rotation_when = g("WANCHAIN_LOG_ROTATION_WHEN", base.get("log_rotation_when"))
    interval_raw = g(
        "WANCHAIN_LOG_ROTATION_INTERVAL",
        base.get("log_rotation_interval", 1),
    )
    interval = _to_int(interval_raw) or 1
    log_rotation_utc = _parse_bool(
        g("WANCHAIN_LOG_ROTATION_UTC", base.get("log_rotation_utc", False)),
        False,
    )

    return Config(
        enabled=enabled,
        bundle=bundle,
        trace_sampling=trace_sampling,
        otlp_endpoint=otlp_endpoint,
        console_spans=console_spans,
        log_level=log_level,
        log_json=log_json,
        boundary_allow=boundary_allow,
        metrics_enabled=metrics_enabled,
        dev_peek_max_rows=dev_peek_max_rows,
        enable_redaction=enable_redaction,
        redact_keys=redact_keys,
        unicode_safe=unicode_safe,
        strip_emoji=strip_emoji,
        force_utf8=force_utf8,
        log_rotation_enabled=log_rotation_enabled,
        log_rotation_path=str(log_rotation_path) if log_rotation_path is not None else None,
        log_rotation_max_bytes=max_bytes,
        log_rotation_backup_count=backup_count,
        log_rotation_when=str(log_rotation_when) if log_rotation_when is not None else None,
        log_rotation_interval=interval,
        log_rotation_utc=log_rotation_utc,
    )
