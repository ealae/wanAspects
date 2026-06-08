"""End-to-end test of the in-process `file` exporters (air-gapped path).

Runs a fresh subprocess so the global OpenTelemetry providers are pristine, then
asserts wanaspects wrote valid JSONL traces + logs to ``WANCHAIN_TELEMETRY_DIR``
with trace/log correlation — no collector, no network.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("opentelemetry.sdk._logs")

_EMITTER = """
import logging
from wanaspects import init_telemetry
init_telemetry()
from opentelemetry import trace
from opentelemetry._logs import get_logger_provider

log = logging.getLogger("filetest")
tracer = trace.get_tracer("filetest")
with tracer.start_as_current_span("filespan"):
    log.info("filelog-inside-span")

trace.get_tracer_provider().force_flush()
get_logger_provider().force_flush()
"""


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_file_exporters_write_correlated_jsonl(tmp_path: Path) -> None:
    env = {
        "WANCHAIN_ASPECTS_ENABLED": "true",
        "WANCHAIN_LOGS_EXPORTER": "file",
        "WANCHAIN_TRACES_EXPORTER": "file",
        "WANCHAIN_TELEMETRY_DIR": str(tmp_path),
        "WANCHAIN_LOG_LEVEL": "INFO",
        "WANCHAIN_TRACE_SAMPLING": "1.0",
        "SERVICE_NAME": "svc",
        "PATH": os.environ.get("PATH", ""),
    }
    result = subprocess.run(
        [sys.executable, "-c", _EMITTER],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    log_files = list(tmp_path.glob("svc.*.logs.jsonl"))
    trace_files = list(tmp_path.glob("svc.*.traces.jsonl"))
    assert log_files, f"no log file written; stderr={result.stderr}"
    assert trace_files, f"no trace file written; stderr={result.stderr}"

    logs = _read_jsonl(log_files[0])
    spans = _read_jsonl(trace_files[0])

    log_rec = next(r for r in logs if r.get("body") == "filelog-inside-span")
    span = next(s for s in spans if s.get("name") == "filespan")

    # The log emitted inside the span must carry that span's trace id.
    assert log_rec["trace_id"] == span["context"]["trace_id"]
