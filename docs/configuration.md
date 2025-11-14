# Configuration & Diagnostics

## Precedence
- Environment variables override `pyproject.toml` settings.
- If environment variables are unset, values fall back to `[tool.wanchain.aspects]` in `pyproject.toml`.

## Supported Keys

| pyproject key | Environment variable | Type / Default | Notes |
| --- | --- | --- | --- |
| `enabled` | `WANCHAIN_ASPECTS_ENABLED` | bool / `false` | Global on/off switch required to initialize telemetry. |
| `bundle` | `WANCHAIN_ASPECTS_BUNDLE` | str / `"default"` | `default`, `dev`, or `prod`. |
| `trace_sampling` | `WANCHAIN_TRACE_SAMPLING` | float / `0.0` | 0..1 fraction. Recommended: `0.1` staging, `0.0` prod. |
| `otlp_endpoint` | `WANCHAIN_OTLP_ENDPOINT` | str / `None` | OTLP HTTP endpoint (collector or vendor). |
| `console_spans` | `WANCHAIN_OTEL_CONSOLE` | bool / `false` | Print spans to stdout (local demos). |
| `log_level` | `WANCHAIN_LOG_LEVEL` | str / `"INFO"` | Stdlib logging level for `wanaspects` logger. |
| `log_json` | `WANCHAIN_LOG_JSON` | bool / `true` | JSON renderer when structlog is installed; falls back to key/value otherwise. |
| `boundary_allow` | `WANCHAIN_BOUNDARY_ALLOW` | list/CSV / `["geo","io"]` | Allowed boundary types that may materialize. |
| `metrics_enabled` | `WANCHAIN_METRICS_ENABLED` | bool / `false` | Enables metrics collection when tracing/logging are on. |
| `dev_peek_max_rows` | `WANCHAIN_DEV_PEEK_MAX_ROWS` | int / `None` | Caps `.peek()` preview rows in dev; ignored when unset. |
| `enable_redaction` | `WANCHAIN_ENABLE_REDACTION` | bool / `true` | Attach the redaction filter that masks sensitive keys before logging. |
| `redact_keys` | `WANCHAIN_REDACT_KEYS` | list/CSV / `[]` | Additional keys (beyond defaults) to scrub when redaction is enabled. |
| `unicode_safe` | `WANCHAIN_UNICODE_SAFE` | bool / `true` | Wrap console handlers with a Unicode-safe formatter that prevents encode crashes. |
| `strip_emoji` | `WANCHAIN_STRIP_EMOJI` | optional bool / `None` | `true` strips emoji, `false` keeps them, `None` strips only for non-UTF-8 streams. |
| `force_utf8` | `WANCHAIN_FORCE_UTF8` | bool / `false` | Re-encode console output as UTF-8 even if the stream advertises another codec. |
| `log_rotation_enabled` | `WANCHAIN_LOG_ROTATION_ENABLED` | bool / `false` | Manage a rotating file handler alongside console logging. |
| `log_rotation_path` | `WANCHAIN_LOG_ROTATION_PATH` | str / `None` | Absolute or relative path for the rotated log file. |
| `log_rotation_max_bytes` | `WANCHAIN_LOG_ROTATION_MAX_BYTES` | int / `10485760` | Trigger rotation after this many bytes (default 10 MiB). |
| `log_rotation_backup_count` | `WANCHAIN_LOG_ROTATION_BACKUP_COUNT` | int / `5` | Number of historical log files to retain. |
| `log_rotation_when` | `WANCHAIN_LOG_ROTATION_WHEN` | str / `None` | Use time-based rotation (e.g., `"midnight"`) instead of size. Leave unset to rotate by size. |
| `log_rotation_interval` | `WANCHAIN_LOG_ROTATION_INTERVAL` | int / `1` | Multiplier for time-based rotation cadence. |
| `log_rotation_utc` | `WANCHAIN_LOG_ROTATION_UTC` | bool / `false` | Evaluate time-based rotation in UTC instead of local time. |

## pyproject Example
```toml
[tool.wanchain.aspects]
enabled = true
bundle = "default"
trace_sampling = 0.1
otlp_endpoint = "http://localhost:4318/v1/traces"
console_spans = true
log_level = "INFO"
log_json = true
boundary_allow = ["geo", "io"]
metrics_enabled = true
dev_peek_max_rows = 50
enable_redaction = true
redact_keys = ["password", "ssn"]
unicode_safe = true
strip_emoji = "auto"  # "auto"/None => strip when stream encoding is not UTF-8
force_utf8 = false
log_rotation_enabled = true
log_rotation_path = "logs/wanaspects.log"
log_rotation_max_bytes = 10485760
log_rotation_backup_count = 7
log_rotation_when = "midnight"
log_rotation_interval = 1
log_rotation_utc = false
```

## Diagnostics
- Print the resolved configuration and derived state:
  ```
  python -m wanaspects.diag
  ```
- For a full quality gate (lint/mypy/tests) run `python scripts/run_quality_gates.py` which delegates to `poetry run ...`.
