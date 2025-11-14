# Examples

Minimal examples to demonstrate telemetry output controlled by environment variables.

## Telemetry Demo

Runs a simple step wrapped by the default aspect bundle, with optional logs and traces.

### 1) Install

```
pip install -e .[dev]
```

### 2) Enable telemetry via environment

PowerShell (Windows):

```
$env:WANCHAIN_ASPECTS_ENABLED = 'true'
$env:WANCHAIN_TRACE_SAMPLING = '0.1'         # staging default (use 0.0 in prod)
$env:WANCHAIN_OTEL_CONSOLE = 'true'          # print spans to console (demo only)
```

### 3) Run

```
python examples/telemetry_demo.py
```

Expected:
- Structured log events (step_start, step_end) with `step`, `shape`, `boundary`, `status`.
- Console span output if OpenTelemetry is installed and `WANCHAIN_OTEL_CONSOLE=true`.

To send spans to an OTLP endpoint (optional):

```
$env:WANCHAIN_OTLP_ENDPOINT = 'http://localhost:4318/v1/traces'
python examples/telemetry_demo.py
```

Unset `WANCHAIN_ASPECTS_ENABLED` or set it to `false` to disable telemetry quickly.

## No-Collect Guard Demo

Demonstrates strict boundary enforcement when materializing:

```
python examples/materialize_demo.py
```

First step runs with `boundary='none'` and raises `ContractViolation` when calling `materialize(...)`.
Second step sets `boundary='io'` and the same call succeeds.

## Diagnostics

Print the active configuration and derived state:

```
python -m wanaspects.diag
```
