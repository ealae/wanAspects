# Repository Guidelines

## Project Structure & Module Organization
- Python package metadata lives in `pyproject.toml` (Python 3.10+).
- Source code should live under `src/wanaspects/` (create as needed); package name is `wanaspects`.
- Tests belong in `tests/` (e.g., `tests/test_example.py`).
- Project management and planning docs (ADR, PRD, proposal bundle) now live under `docs/_internal/project-management/`; see that folder’s README for details.
- Internal tooling (quality gates, release helpers, doc scripts) live under `scripts/_internal/`.

## Build, Test, and Development Commands
- Install editable for local dev: `pip install -e .`
- Build a wheel/sdist (requires `build`): `python -m build`
- Run the full quality gate (format, lint, types, tests): `python scripts/_internal/check.py` (add `--fix` to auto-format)
- Run tests (when present): `pytest -q`
- Lint only: `ruff format --check . && ruff check .`
- Type-check only: `mypy --strict src/wanaspects`
- Diagnostics entrypoint: `python -m wanaspects.diag`

## Planning Docs Workflow
- All ADR/PRD/proposal artifacts live in `docs/_internal/project-management/`.
- Keep `docs/_internal/project-management/toc.yml` accurate by running `python docs/_internal/project-management/scripts/verify-toc.py --toc-path docs/_internal/project-management/toc.yml` (or the PowerShell equivalent).
- Update ADRs/PRDs directly in that folder; the old `.specify` scaffolding scripts and `specs/###-feature/` outputs were removed—do not recreate them.

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indent, type hints for public APIs, module/function `snake_case`, classes `PascalCase`, constants `UPPER_CASE`.
- Package layout: `src/wanaspects/<module>.py`; avoid giant modules; prefer small, testable functions.
- If formatters/linters are available locally, use `black` and `ruff`; otherwise keep style consistent.

## Testing Guidelines
- Framework: `pytest`.
- Location and names: `tests/test_*.py`; mirror package structure (e.g., `src/wanaspects/utils.py` → `tests/test_utils.py`).
- Write tests per functional requirement; use fixtures over globals; add regression tests for bugs.

## Commit & Pull Request Guidelines
- Branch names: scripts generate `NNN-short-title` (e.g., `001-init-spec`). If manual, follow the same pattern.
- Commits: concise, imperative (“Add parser”), optionally prefix with feature id (e.g., `001: Add parser`).
- PRs: include purpose, scope, and links to relevant spec/plan (e.g., `specs/001-init-spec/spec.md`), screenshots or sample logs when UI/CLI behavior changes, and clear validation steps.

## Agent & Spec Workflow
- Operate from repo root and prefer absolute paths as prompts suggest.
- Keep clarifications in specs limited and high-impact; update the planning docs before implementation to reflect decisions.
