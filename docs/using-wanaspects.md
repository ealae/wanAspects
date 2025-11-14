# Using `wanaspects` in Your Pipeline

This guide walks you through installing the package, enabling telemetry, wiring it into a workflow, validating guardrails, and exporting data to a collector. Follow the steps in order; each builds on the previous one.

---

## 1. Install & Prepare the Environment
```bash
poetry install  # or: pip install -e .
poetry run python -m pip install opentelemetry-exporter-otlp  # optional exporters
```

- Prefer Poetry (`python scripts/run_quality_gates.py` wraps lint/mypy/tests).
- Ensure Python ≥ 3.10.
- If you use `pip`, remember to add `src/` to `PYTHONPATH` for local demos.

---

## 2. Initialize Telemetry at Application Start
```python
from wanaspects import init_telemetry

init_telemetry()  # no-op unless WANCHAIN_ASPECTS_ENABLED=true (or pyproject enabled)
```

Environment toggles (see `docs/configuration.md` for full list):
- `WANCHAIN_ASPECTS_ENABLED=true`
- `WANCHAIN_TRACE_SAMPLING=0.1` (staging) or `0.0` (prod)
- `WANCHAIN_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces` (collector)
- `WANCHAIN_OTEL_CONSOLE=true` (local demo)

Use `python -m wanaspects.diag` to confirm resolved settings.

---

## 3. Wrap Steps with the Aspect Manager

**Development / Testing:**
```python
from wanaspects import OptimizedAspectManager, dev_bundle
from wanaspects.core.context import AdviceContext
from wanaspects.guards import materialize

# Use OptimizedAspectManager for better performance
aspect_manager = OptimizedAspectManager(dev_bundle())

def step_lazy(ctx: AdviceContext) -> str:
    # Raises ChainContractError unless boundary != "none"
    return materialize(lambda: "collected!")

ctx = AdviceContext(
    step_name="ingest_geo",
    container_shape="batch",
    boundary="geo",
    run_id="run-123",
    tenant="ca-east",
    package_versions={"wanaspects": "0.1.0"},
)

result = aspect_manager.run(ctx, lambda: step_lazy(ctx))
```

**Production:**
```python
from wanaspects import OptimizedAspectManager, prod_bundle

# Optimized for performance while maintaining full observability
aspect_manager = OptimizedAspectManager(prod_bundle())
```

### Bundle Choices

- **`default_bundle()`**: Full observability with all aspects
  - Context propagation, logging, tracing, metrics, contract validation
  - Best for: Development, testing, debugging
  - Performance: ~150x overhead (acceptable for non-production)

- **`dev_bundle()`**: Development-optimized bundle
  - Full verbose logging for debugging
  - All aspects enabled including contracts
  - Best for: Local development, troubleshooting
  - Performance: ~150x overhead

- **`prod_bundle()`**: Production-optimized bundle ⭐ **RECOMMENDED**
  - Smart logging (errors + boundaries only)
  - Sampled metrics (10% sampling, 100% errors)
  - Conditional context (boundaries only)
  - No contract validation (use in dev/test)
  - Best for: Production deployments
  - Performance: **~60x overhead** ✅
  - Observability: **100% errors, boundaries, tracing tracked**

### Custom Bundles

Build your own for specific needs:
```python
from wanaspects import (
    OptimizedAspectManager,
    ConditionalContextPropagationAspect,
    SmartLoggingAspect,
    TracingAspect,
    SampledMetricsAspect,
)

# Hot path bundle (minimal overhead, ~25x)
hot_path = OptimizedAspectManager([TracingAspect()])

# Custom production bundle with 5% metrics sampling
custom_prod = OptimizedAspectManager([
    ConditionalContextPropagationAspect(),
    SmartLoggingAspect(tier="production"),
    TracingAspect(),
    SampledMetricsAspect(sample_rate=0.05),  # 5% sampling
])
```

### Manager Choices

- **`AspectManager`**: Standard manager (use for compatibility)
- **`OptimizedAspectManager`**: Optimized version with fast paths ⭐ **RECOMMENDED**
  - 5.4x faster with no aspects
  - Fast paths for 0 and 1 aspect cases
  - Use this for all new code

---

## 4. Understanding prod_bundle() Performance Optimizations

The `prod_bundle()` achieves **~60x overhead** (vs 200x+ for default) while maintaining comprehensive observability through smart conditional execution:

### What You Still Get (100% Coverage)

✅ **100% Error Logging** - Every failure logged with full context
✅ **100% Boundary Logging** - All service entry/exit points tracked
✅ **100% Distributed Tracing** - Full OpenTelemetry spans
✅ **100% Error Metrics** - Every failure in counters/histograms
✅ **10% Success Metrics** - Statistical sampling (more than enough!)
✅ **Context at Boundaries** - Available for trace correlation

### What Gets Skipped (Performance)

❌ **Verbose internal logging** - Millions of identical "step_start → step_end" for successful internal calls
❌ **Context for internal calls** - Only propagated at boundaries where needed
❌ **Contract validation** - Use `dev_bundle()` in development/testing

### Optimized Aspects

**SmartLoggingAspect(tier="production")**:
- Skips verbose logging for successful internal calls
- Always logs errors and boundary events
- 51% faster for internal calls

**SampledMetricsAspect(sample_rate=0.1)**:
- Records 10% of successful calls (configurable)
- Always records 100% of errors
- Reduces metrics overhead by ~70%

**ConditionalContextPropagationAspect()**:
- Only propagates context at service boundaries
- Propagates when trace_id present (for correlation)
- Reduces context overhead by ~75%

### Example: What Gets Logged

```python
# Internal helper function (succeeds)
result = manager.run(internal_ctx, lambda: process_data(x))
# Captured: OTel span, metrics (10% chance)
# Skipped: Log messages (too noisy)

# API endpoint (boundary="entry")
result = manager.run(boundary_ctx, lambda: handle_request(req))
# Captured: Log, OTel span, metrics, context
# Everything tracked at boundaries!

# Any error
result = manager.run(ctx, lambda: might_fail())  # raises
# Captured: Error log, error metrics, span with error, context
# 100% error coverage always!
```

For detailed performance analysis, see `OPTIMIZATION_SUCCESS.md` in the repository root.

---

## 5. Mark Boundaries & Respect Guardrails
- Default boundary is `"none"`: materialization raises `ChainContractError`.
- Allowed values: `"geo"`, `"io"`, or `"none"`. Set `ctx.boundary` accordingly.
- `WANCHAIN_BOUNDARY_ALLOW` restricts which boundary types are legal.
- ContractAspect validates boundary values and manages materialization context.

Quick regression tests:
```bash
poetry run pytest tests/aspects/test_no_collect_guard.py
poetry run pytest tests/aspects/test_logging.py  # checks correlation fields
```

---

## 6. Export Logs, Traces, and Metrics
1. **Logs** – emitted via the stdlib `logging` API, enhanced when structlog is available. Fields include `step`, `shape`, `boundary`, `status`, `run_id`, `tenant`, `trace_id`, `span_id`, `duration_ms`, and `error.*`.
2. **Traces** – OpenTelemetry spans with attributes (`wanchain.step.name`, etc.). Sampling is controlled via configuration; defaults keep load low.
3. **Metrics** – Counters and histograms (`wanchain_steps_total`, `wanchain_step_errors_total`, `wanchain_step_duration_seconds`). Labels stay low-cardinality (`step`, `shape`, `boundary`, `status`).

Example environment for OTLP exporter:
```powershell
$env:WANCHAIN_ASPECTS_ENABLED = 'true'
$env:WANCHAIN_OTLP_ENDPOINT = 'http://otel-collector:4318/v1/traces'
$env:WANCHAIN_TRACE_SAMPLING = '0.1'
python examples/telemetry_demo.py
```

The OpenTelemetry Collector can receive those spans/metrics and forward them to Jaeger, Prometheus, or another observability backend.

---

## 7. Harden Logging Output

Structured logging is now resilient by default, but you can tune the behaviour further:

- **Redaction filter** – enabled via `WANCHAIN_ENABLE_REDACTION=true` (default). Add comma-separated keys with `WANCHAIN_REDACT_KEYS` to scrub credentials or tokens automatically. The filter sits on every handler installed by `init_telemetry()`, so logs, cache events, and API helpers all share the same protection.
- **Unicode-safe console formatter** – guard against Windows and legacy terminals failing on emoji or astral plane characters. Keep it on (`WANCHAIN_UNICODE_SAFE=true`) to auto-detect encodings, optionally override stripping with `WANCHAIN_STRIP_EMOJI=true|false`, or force UTF-8 re-encoding with `WANCHAIN_FORCE_UTF8=true` when you control the sink.
- **Rotating file handler** – flip on `WANCHAIN_LOG_ROTATION_ENABLED=true` and point `WANCHAIN_LOG_ROTATION_PATH` at a writable location. Combine size-based (`WANCHAIN_LOG_ROTATION_MAX_BYTES`) and time-based (`WANCHAIN_LOG_ROTATION_WHEN`, `WANCHAIN_LOG_ROTATION_INTERVAL`, `WANCHAIN_LOG_ROTATION_UTC`) limits to keep disk usage predictable.
- **Domain helpers** – import from `wanaspects.aspects.logging_extensions` to avoid ad-hoc schemas:

  ```python
  import logging
  from wanaspects.aspects.logging_extensions import (
      log_api_call,
      log_cache_operation,
      log_db_query,
  )

  logger = logging.getLogger("wanaspects.demo")

  log_db_query(logger, statement="SELECT 1", duration_ms=3.2, row_count=1)
  log_cache_operation(logger, operation="get", key="users:42", hit=True)
  log_api_call(logger, method="GET", url="https://api.example.com", status_code=200)
  ```

  Every helper emits a consistent payload (`db`, `cache_event`, or `api_call`) with success flags and error fields, making dashboards and filters trivial to build.

Consult [`docs/configuration.md`](configuration.md) for every available toggle.

---

## 8. Validate Local Setup
1. Run the demo with console exporter:
   ```powershell
   $env:PYTHONPATH = 'src'
   $env:WANCHAIN_ASPECTS_ENABLED = 'true'
   $env:WANCHAIN_TRACE_SAMPLING = '1.0'
   $env:WANCHAIN_OTEL_CONSOLE = 'true'
   python examples/telemetry_demo.py
   ```
   Expect JSON logs plus span output.
2. Execute the quality gates:
   ```bash
   python scripts/run_quality_gates.py
   ```
3. Inspect diagnostics:
   ```bash
   poetry run python -m wanaspects.diag
   ```

---

## 9. Integrate with Downstream Pipelines
- Wrap each step or decorator with `AspectManager`, supplying the appropriate `AdviceContext`.
- Call `init_telemetry()` once per process (should be a safe no-op when disabled).
- Configure boundary values in your workflow code so ContractAspect permits intentional materializations.
- Feed `run_id`, `tenant`, and version info into `AdviceContext` to enable cross-service correlation.
- Pipe OTLP output into your chosen collector/backends to centralize observability.

For deeper conceptual background, revisit [Telemetry 101](telemetry-101.md). For troubleshooting or advanced configuration, see [Troubleshooting](troubleshooting.md) and [Configuration Reference](configuration.md).
