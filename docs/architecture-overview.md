# Architecture Overview

Core Concepts
- AdviceContext: immutable per-step context with `step`, `shape`, `boundary`, IDs, versions.
- Aspect protocol: `before(ctx)`, `around(ctx, call)`, `after(ctx, result, error)`.
- AspectManager: composes aspects and runs the call through `around` wrappers.

Included Aspects
- LoggingAspect: emits JSON-friendly logs (structlog if available, stdlib logging always) with correlation fields.
- TracingAspect: creates a span per step (OpenTelemetry if installed) and records attributes/errors.
- MetricsAspect: minimal counters by step/shape/boundary/status.
- ContractAspect: validates `boundary` and is the natural place for the no-collect guard.

No-Collect Guard
- Use `from wanaspects.guards import materialize` inside steps to perform explicit materialization.
- ContractAspect allows `materialize(...)` only when the step `boundary != 'none'`; otherwise raises `ContractViolation`.

Boundaries
- Allowed: `none` (default), `geo`, `io`.
- Materialization only at boundary steps; otherwise raise a guard error.

Public API
- `from wanaspects import AspectManager, default_bundle, init_telemetry`
- Call `init_telemetry()` once at application startup to configure telemetry providers
- Create an `AspectManager` with your chosen bundle (default, dev, or prod)
- Wrap steps with `manager.run(ctx, callable)` to apply all aspects

For configuration details and environment variables, see [Configuration Reference](configuration.md).

## Basic Usage Example

```python
from wanaspects import AspectManager, default_bundle, init_telemetry
from wanaspects.core.context import AdviceContext
from wanaspects.guards import materialize

init_telemetry()
manager = AspectManager(default_bundle())
ctx = AdviceContext(step_name="step", container_shape="single", boundary="none")
def step():
    # Raises unless boundary != 'none'
    return materialize(lambda: "ok")
result = manager.run(ctx, step)
```
