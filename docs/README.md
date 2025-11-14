# wanaspects Documentation

A composable aspects library for cross-cutting telemetry concerns in data pipelines: structured logging, distributed tracing, metrics, and boundary contract enforcement.

**What it does:** Provides a consistent way to add observability (logs, traces, metrics) and enforce materialization boundaries in your data processing steps, without scattering instrumentation code throughout your application.

---

## 📖 For Users

### New to Telemetry?

Follow this path to get started:

1. **[Telemetry 101](telemetry-101.md)** - Understand observability concepts, OpenTelemetry, and why telemetry matters
2. **[User Guide](user-guide.md)** - Install the library, enable telemetry, and integrate aspects into your pipeline
3. **[Configuration Reference](configuration.md)** - All settings, environment variables, and configuration options
4. **[Troubleshooting](troubleshooting.md)** - Common issues and their solutions

### Quick Reference

- **[Architecture Overview](architecture-overview.md)** - Core concepts, aspect protocol, and design principles
- **[Examples](../examples/README.md)** - Runnable code samples demonstrating telemetry and boundary guards

---

## 🔧 For Contributors

- **[AGENTS.md](../AGENTS.md)** - Repository-wide guidance for humans and agents contributing to wanAspects
- Prefer Poetry (Python 3.10+) for local development, and run `pytest -q` before opening a PR
- Release owners should follow the private release playbook (ask the release coordinator for access) before mirroring any changes

---

## 📁 Project Structure

- **`src/wanaspects/`** - Library source code
  - `core/` - AdviceContext and Aspect protocol
  - `aspects/` - Logging, tracing, metrics, contract, and context propagation implementations
  - `manager.py` - AspectManager composition
- **`tests/`** - Test suite (unit, aspects, integration)
- **`examples/`** - Demonstration scripts
- **`docs/`** - This documentation
