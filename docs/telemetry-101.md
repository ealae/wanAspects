# Telemetry 101

This guide is a gentle, progressive introduction to the core ideas behind telemetry and- Try the quick demo:  
  `PYTHONPATH=src WANCHAIN_ASPECTS_ENABLED=true WANCHAIN_OTEL_CONSOLE=true python examples/telemetry_demo.py`
- Explore [Configuration Reference](configuration.md) for all settings and environment variables once you're comfortable with these fundamentals. we apply them in the `wanaspects` package. Work through the sections in order; each layer adds more detail on top of the previous one.

## 1. Why Telemetry Matters
- **What we are solving**: Data and platform teams need to understand *what* their pipelines are doing, *where* they slow down, and *why* they fail — without sprinkling ad-hoc `print()` or copy/pasting logging setups.
- **Common pain points**: Missing correlation between steps, silent materializations that break lazy semantics, and inconsistent tooling across projects.
- **Goal**: Provide consistent, low-overhead insights (logs, traces, metrics) that travel with each step so teams debug faster while keeping boundary guardrails intact.

## 2. Observability vs Telemetry
- **Observability** is the outcome: the ability to answer questions about a system’s behavior.
- **Telemetry** is the raw signal we emit to reach that outcome. In practice we care about three main signals:
  - **Logs**: discrete event records (e.g., “step_start”, “step_end”).
  - **Metrics**: numeric measurements over time (e.g., step duration histogram).
  - **Traces**: timelines of work with spans linked together (e.g., each chain step as a span).
- `wanaspects` captures all three so you can correlate them later.

## 3. Core Vocabulary
- **Aspect**: A hook (`before`, `around`, `after`) that observes or augments step execution.
- **AdviceContext**: The immutable metadata bundle (step name, boundary, run ID, trace IDs, version info) shared across aspects.
- **Bundle**: A set of aspects wired together (default/dev/prod).
- **Materialization**: Turning a lazy data structure into concrete rows (e.g., `LazyFrame.collect()`). Guarded by `ChainContractError` unless the step declares a boundary.

## 4. OpenTelemetry In A Nutshell
- **Standardized spec** defining concepts for telemetry data across platforms.
- **Language SDKs** (Python, Go, etc.) that instrumentation libraries use to create spans and metrics.
- **Collector**: A standalone service (binary or container) that receives telemetry (OTLP protocol), processes, and exports it to backends (Grafana, Prometheus, Azure Monitor, etc.).
- **Backends / Observability platforms**: Where telemetry is stored, queried, and visualized.

```
Application code
   ↓   (instrumented by wanaspects + OpenTelemetry SDK)
OpenTelemetry SDK
   ↓   (OTLP over gRPC/HTTP)
OpenTelemetry Collector (optional but recommended)
   ↓
Telemetry backend (Jaeger, Prometheus, Elastic, New Relic, …)
```

## 5. Telemetry Pipeline Components
1. **Instrumentation**  
   - `wanaspects` aspects (Logging, Tracing, Metrics, Contract, ContextPropagation) wrap each step.  
   - They populate the `AdviceContext` and emit signals via structlog and the OpenTelemetry SDK.
2. **Exporters**  
   - Lightweight client pieces that ship telemetry to a collector or vendor endpoint.  
   - `wanaspects.telemetry.init_telemetry()` wires OTLP exporters when enabled.
3. **Collector (optional but powerful)**  
   - Receives telemetry from many services.  
   - Can batch, filter, enrich, or route data to multiple destinations.  
   - Decouples your app from vendor-specific SDKs.
4. **Backends**  
   - Long-term home for telemetry (e.g., Azure Monitor, Prometheus, Jaeger).  
   - Enable dashboards, alerting, trace exploration.

## 6. OpenTelemetry Architecture Deeper Dive
- **SDK Layer**  
  - Handles span lifecycle, context propagation, and metrics instruments.  
  - In Python, the tracer provider uses samplers and span processors.
- **Span Processors**  
  - Intercept spans after they end (e.g., `BatchSpanProcessor` flushes them in batches).  
  - `wanaspects` registers processors depending on configuration (OTLP exporter, console exporter).
- **Sampler**  
  - Decides which traces to keep (TraceIdRatioBased in our defaults).  
  - Critical for meeting the <5% overhead budget.
- **Resource Attributes**  
  - Describe the service emitting telemetry (e.g., `service.name = "wanaspects"`).  
  - Useful for multi-service environments.
- **Collector Pipelines**  
  - Built from receivers (ingest OTLP), processors (batch, tail sampling), exporters (send to backend).  
  - Configure via YAML; can have multiple pipelines per signal type.

## 7. How Correlation Works
- **ContextPropagationAspect** pushes the current `AdviceContext` into `contextvars`.  
- **TracingAspect** creates spans using trace and span IDs. These IDs flow into logs/metrics by reading the current context.  
- **LoggingAspect** emits fields like `trace_id`, `span_id`, `run_id`, `boundary`, `duration_ms`, and error metadata so you can connect logs to spans.  
- **MetricsAspect** keeps low-cardinality labels (`step`, `shape`, `boundary`, `status`) and records error counters separately (`error_kind`).

## 8. Safety & Performance Guardrails
- **ChainContractError** prevents accidental materialization unless a step declares a boundary (`boundary="geo"` / `"io"`).
- **Sampling defaults**: 0% in production, 10% in staging (configurable via env/pyproject).
- **Telemetry disabled by default**: ensure near-zero overhead until toggled on.
- **Low cardinality**: metrics avoid dimensions that explode label counts (no per-run IDs).
- **Log hygiene**: the redaction filter scrubs secrets, the Unicode-safe formatter shields non-UTF-8 sinks, and optional rotation keeps file handlers from ballooning.

## 9. Rolling Telemetry Out
1. **Staging Trial**  
   - Enable aspects with `WANCHAIN_ASPECTS_ENABLED=true`.  
   - Point `WANCHAIN_OTEL_CONSOLE=true` for quick console spans or configure `WANCHAIN_OTLP_ENDPOINT` for collector.  
   - Validate `wanaspects.diag` output before rollout.
2. **Collector Setup (Optional)**  
   - Deploy OpenTelemetry Collector near your workloads.  
   - Configure OTLP receiver, batching processor, exporter (e.g., to Azure Monitor or Jaeger).  
   - Update environment to point at the collector URL.
3. **Production**  
   - Lower sampling (`WANCHAIN_TRACE_SAMPLING=0.0` or small fraction).  
   - Monitor metrics dashboards for overhead and guardrail alerts.  
   - Document boundaries in step definitions to avoid lazy violations.

## 10. Putting It All Together
- **You toggle telemetry** → `init_telemetry()` configures structlog & tracing based on env/pyproject.  
- **AspectManager** runs the default bundle → context is propagated, logs/traces/metrics emitted with stable metadata.  
- **OTLP exporter** ships spans/metrics → collector (or backend) stores them.  
- **Ops & Data teams** gain shared visibility: consistent logs, distributed traces, guardrails on materialization, and metrics for alerting.

## 11. Next Steps

- Try the quick demo:  
  `PYTHONPATH=src WANCHAIN_ASPECTS_ENABLED=true WANCHAIN_OTEL_CONSOLE=true python examples/telemetry_demo.py`
- Explore [Configuration Reference](configuration.md) for all settings and environment variables once you're comfortable with these fundamentals.
