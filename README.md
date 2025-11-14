# wanAspects

Cross-cutting aspects for Wan* pipelines: structured logging, tracing, metrics, and contract guardrails built on top of OpenTelemetry.

- See `docs/telemetry-101.md` for a newcomer-friendly introduction to telemetry concepts.
- For quickstart instructions, visit `docs/user-guide.md`.

This README exists at the repository root so Poetry can package the project successfully.

## Public release notes

This project uses an allowlist-based approach to control what is mirrored publicly. The `.public-release-include` file in the repository root lists content that may be included in a public release. Any path segment that begins with an underscore (for example: `_internal/`) is considered internal and will be excluded from public releases by default.

Maintainers only: internal release and scanning tools remain in the private toolchain; use those private utilities to validate and perform the public sync.

## License & Changelog

wanAspects is dual-licensed:

- **GPL-3.0-or-later** — see the canonical text at <https://www.gnu.org/licenses/gpl-3.0.txt>.
- **Commercial License** — contact `ealae_ehanu@proton.me` to obtain proprietary terms.

See `LICENSE.md` for guidance on choosing the option that fits your deployment, and `CHANGELOG.md` for release history.
