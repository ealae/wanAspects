# User Guide

This guide combines the quickstart, pipeline integration, and validation steps for `wanaspects`. Follow the sections in order to install the library, enable telemetry, wire it into your workflow, and confirm everything is working.

---

## 1. Prerequisites & Installation

- Python 3.10+
- PowerShell (Windows) or a POSIX shell
- Optional: Poetry for dependency management

```bash
# Clone the repository
git clone https://gitlab.k8s.cloud.statcan.ca/jeanphilippe.wan/wanaspects.git
cd wanAspects

# Create a virtual environment (Windows example)
python -m venv .venv
. .venv/Scripts/activate

# Install dependencies
pip install -e .[dev]
# or, if you prefer Poetry
poetry install
```

Run the quality gates once to ensure the environment is healthy:

```bash
python scripts/_internal/check.py --fix  # format, lint, type-check, and run tests
pytest -q                    # run the test suite directly when iterating
```

---

## 2. Initialize Telemetry

`wanaspects` is inert until telemetry is enabled. At process start, configure and initialize telemetry:

```python
from wanaspects import init_telemetry

init_telemetry()  # no-op unless telemetry is enabled via configuration
```

Useful environment variables (see [Configuration Reference](configuration.md) for the full list):

- `WANCHAIN_ASPECTS_ENABLED=true` – turn the aspects bundle on
- `WANCHAIN_TRACE_SAMPLING=0.1` – adjust tracing volume (0 disables tracing)
- `WANCHAIN_OTEL_CONSOLE=true` – emit traces to the console during local development
- `WANCHAIN_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces` – send data to an OTLP collector

Inspect the resolved configuration at any time:

```bash
python -m wanaspects.diag
```

---

## 3. Wrap Steps with the Aspect Manager

Use `OptimizedAspectManager` (recommended) to apply logging, tracing, metrics, and contract aspects:

**Development:**
```python
from wanaspects import OptimizedAspectManager, dev_bundle
from wanaspects.core.context import AdviceContext
from wanaspects.guards import materialize

# Full verbose logging for debugging
aspect_manager = OptimizedAspectManager(dev_bundle())

ctx = AdviceContext(
    step_name="ingest_geo",
    container_shape="batch",
    boundary="geo",
    run_id="run-123",
    tenant="ca-east",
    package_versions={"wanaspects": "0.1.0"},
)

result = aspect_manager.run(ctx, lambda: materialize(lambda: "collected!"))
```

**Production:**
```python
from wanaspects import OptimizedAspectManager, prod_bundle

# Optimized for performance (~60x overhead vs ~150x for dev)
aspect_manager = OptimizedAspectManager(prod_bundle())
```

### Bundle Choices

- **`default_bundle()`** – Full observability (context, logging, tracing, metrics, contracts)
  - Best for: Development, testing
  - Performance: ~150x overhead

- **`dev_bundle()`** – Development bundle with verbose logging
  - Full logging for debugging
  - All aspects including contracts
  - Performance: ~150x overhead

- **`prod_bundle()`** ⭐ **RECOMMENDED for production**
  - Smart logging (errors + boundaries only)
  - Sampled metrics (10% sampling, 100% errors)
  - Conditional context (boundaries only)
  - No contract validation
  - Performance: **~60x overhead**
  - **Still tracks 100% of errors, boundaries, and traces!**

### Manager Options

- `AspectManager` – Standard manager (backward compatible)
- `OptimizedAspectManager` ⭐ **RECOMMENDED** – Optimized with fast paths (5.4x faster)

For performance details and custom bundles, see `OPTIMIZATION_SUCCESS.md` in the repository root.

See the [Architecture Overview](architecture-overview.md) for deeper context about the aspect protocol and core concepts.

---

## 4. Respect Materialization Boundaries

The `ContractAspect` enforces when a step may materialize results. Key rules:

- Default boundary is `"none"`; calling `materialize(...)` raises an error in that case
- Allowed boundary values: `"none"`, `"geo"`, and `"io"`
- `WANCHAIN_BOUNDARY_ALLOW` can restrict the allowed boundaries at runtime
- `examples/materialize_demo.py` illustrates a permitted materialization

Quick regression checks:

```bash
poetry run pytest tests/aspects/test_no_collect_guard.py
poetry run pytest tests/aspects/test_logging.py
```

---

## 5. Observe Logs, Traces, and Metrics

Once telemetry is enabled:

1. **Logs** – emitted through the standard library `logging` API (enhanced when `structlog` is available) with correlation fields such as `step`, `shape`, `boundary`, `status`, `run_id`, `tenant`, `trace_id`, and `span_id`.
2. **Traces** – OpenTelemetry spans capture timings and attributes like `wanchain.step.name`. Sampling is governed by `WANCHAIN_TRACE_SAMPLING`.
3. **Metrics** – Counters and histograms (`wanchain_steps_total`, `wanchain_step_errors_total`, `wanchain_step_duration_seconds`) stay low-cardinality by design.

Example local demo with console exporters:

```powershell
$env:WANCHAIN_ASPECTS_ENABLED = 'true'
$env:WANCHAIN_TRACE_SAMPLING = '1.0'
$env:WANCHAIN_OTEL_CONSOLE = 'true'
python examples/telemetry_demo.py
```

To forward telemetry to a collector:

```powershell
$env:WANCHAIN_ASPECTS_ENABLED = 'true'
$env:WANCHAIN_OTLP_ENDPOINT = 'http://otel-collector:4318/v1/traces'
$env:WANCHAIN_TRACE_SAMPLING = '0.1'
python examples/telemetry_demo.py
```

Refer to [Telemetry 101](telemetry-101.md) for a conceptual primer and the OTLP pipeline overview.

---

## 6. Validate Your Setup

1. Run the demo script (console or OTLP exporter examples above) and confirm logs + spans appear.
2. Execute quality gates before opening a pull request:
   ```bash
   python scripts/run_quality_gates.py
   ```
3. Inspect diagnostics (`python -m wanaspects.diag`) to confirm configuration and optional dependencies.

---

## 7. Next Steps

- Dive into [Configuration Reference](configuration.md) for advanced tuning
- Consult [Troubleshooting](troubleshooting.md) for common issues
- Review [Telemetry 101](telemetry-101.md) and [Architecture Overview](architecture-overview.md) to understand the design
- Contributors should read the internal [Development Workflow](./_internal/dev-workflow.md) and [Contributing Guide](./_internal/CONTRIBUTING.md)

With these steps, you have a streamlined path from installation to full telemetry integration.
