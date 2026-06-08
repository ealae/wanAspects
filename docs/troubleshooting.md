# Troubleshooting & FAQ

Imports fail (ModuleNotFoundError: wanaspects)
- Ensure the source is on PYTHONPATH: run tests via repo root (we add `src/` in `tests/conftest.py`), or `pip install -e .`.

Pytest complains about coverage options
- Install dev extras: `pip install -e .[dev]` or run tests with `pytest -q`. The coverage gate mirrors the CI `pytest` invocation and is enforced by the standard quality commands.

Mypy cannot find structlog/opentelemetry
- We ignore missing type stubs for these optional packages in `pyproject.toml`. Install them or continue; runtime behavior no-ops if absent.

No spans/logs appear
- Confirm env: `WANCHAIN_ASPECTS_ENABLED=true`.
- For traces: set `WANCHAIN_TRACE_SAMPLING` to `0.1` (staging). Use `WANCHAIN_OTEL_CONSOLE=true` for console spans, or set `WANCHAIN_OTLP_ENDPOINT` to a collector.
- Logs use stdlib logging; ensure you configured handlers/level (see example).
- Print active config: `python -m wanaspects.diag`.

Boundary errors
- Only `none|geo|io` are valid. Mark boundary steps explicitly; materialization is only allowed at boundaries.
- If you hit `ContractViolation` when collecting, wrap the operation with `materialize(lambda: ...)` and set a boundary.

Ruff/mypy failures
- Run `ruff format --check . && ruff check . && mypy --strict src/wanaspects && pytest -q` to verify formatting, lint, types, and tests.
- Use `ruff format .` when you want to apply formatting fixes before re-running the sweep.
