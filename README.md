# wanAspects

Cross-cutting aspects for Wan* pipelines: structured logging, tracing, metrics, and contract guardrails built on top of OpenTelemetry.

- See `docs/telemetry-101.md` for a newcomer-friendly introduction to telemetry concepts.
- For quickstart instructions, visit `docs/user-guide.md`.
- For the full configuration reference, see `docs/configuration.md`.

## Install

```bash
pip install wanaspects
```

or from a local checkout:

```bash
pip install -e .
```

Optional exporters are extras (only needed for the OTLP / Prometheus paths — the
in-process `file` exporters use the core SDK and need nothing extra):

```bash
pip install "wanaspects[otlp]"        # push logs/traces/metrics to a collector
pip install "wanaspects[prometheus]"  # expose / push metrics for Prometheus
```

## Configuration

Everything is configured through environment variables (or a `[tool.wanchain.aspects]`
table in `pyproject.toml`; env wins). Telemetry is **off by default** — nothing
is emitted until you flip the master switch.

```python
from wanaspects import init_telemetry

init_telemetry()  # safe to call repeatedly; a no-op until enabled
```

### 1. Turn it on

| Variable | Default | What it does |
|----------|---------|--------------|
| `WANCHAIN_ASPECTS_ENABLED` | `false` | Master switch. Required before anything is emitted. |
| `WANCHAIN_ASPECTS_BUNDLE` | `default` | `default`, `dev` (full logging), or `prod` (sampled, errors+boundaries). |
| `WANCHAIN_LOG_LEVEL` | `INFO` | Minimum level captured/forwarded. |
| `SERVICE_NAME` | `wanaspects` | Identifies the service in every signal — **set this per service**. |

### 2. Centralize logs + traces

Pick **one** of two sinks. Both produce the same JSONL and the same log↔trace
correlation (`trace_id` is stamped on every log emitted inside a step).

**a) In-process files — no collector, works air-gapped (recommended for offline):**

```bash
export WANCHAIN_ASPECTS_ENABLED=true
export WANCHAIN_LOGS_EXPORTER=file
export WANCHAIN_TRACES_EXPORTER=file
export WANCHAIN_TELEMETRY_DIR=/var/log/wan   # shared dir for all services
export SERVICE_NAME=wanelf                    # wanparser, wanparser-orchestration, …
```

Each process writes `<service>.<pid>.<signal>.jsonl` into `WANCHAIN_TELEMETRY_DIR`.
Point every service at the **same directory** and they are centralized — query
with `grep`/`jq` across `*.jsonl`. No binary, no network, no extra package.

**b) OTLP — push to an OpenTelemetry Collector (multi-host / scale-up):**

```bash
export WANCHAIN_ASPECTS_ENABLED=true
export WANCHAIN_OTLP_ENDPOINT=http://127.0.0.1:4318   # base URL; /v1/<signal> added
export WANCHAIN_LOGS_EXPORTER=otlp                    # needs the [otlp] extra
# traces auto-use OTLP when WANCHAIN_OTLP_ENDPOINT is set
export WANCHAIN_TRACE_SAMPLING=1.0
```

### 3. Metrics (optional)

```bash
export WANCHAIN_METRICS_ENABLED=true
export WANCHAIN_METRICS_EXPORTER=prometheus   # or: otlp
export WANCHAIN_METRICS_PORT=9464             # standalone scrape port for non-ASGI services
```

ASGI hosts (e.g. FastAPI) instead mount `/metrics` directly via `prometheus_client`.

### Full reference

`docs/configuration.md` lists every variable (redaction, Unicode-safe console,
log rotation, trace sampling, dev peek limits, …) with defaults.

## Querying the `file` output

The in-process `file` exporter writes one flat OTel record per line:

```bash
# Errors with their trace id
jq -r 'select(.severity_text=="ERROR") | "\(.trace_id)  \(.body)"' /var/log/wan/*.logs.jsonl

# Spans for one trace id (the bug-hunting waterfall)
jq -r --arg t "0x<TRACE_ID>" 'select(.context.trace_id==$t) | "\(.name) \(.status.status_code)"' \
  /var/log/wan/*.traces.jsonl
```

Debug loop: filter `*.logs.jsonl` to the error → copy its `trace_id` → list that
trace's spans in `*.traces.jsonl` to see which step/boundary failed.

## Changelog

See `CHANGELOG.md` for release history.

## License

wanAspects is dual-licensed under **GPL-3.0-or-later** or a commercial agreement (contact `ealae_ehanu@proton.me`).
