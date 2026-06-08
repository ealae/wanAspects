# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-06-08
- Added file and OTLP exporters for logs and traces so telemetry is actually
  emitted: global Meter/Logger providers plus a stdlib→OTel logging bridge.
- New `WANCHAIN_*` exporter knobs: `logs_exporter`/`traces_exporter=file` writes
  in-process JSONL (air-gapped, no collector) to `WANCHAIN_TELEMETRY_DIR`;
  `=otlp` pushes to a collector via `WANCHAIN_OTLP_ENDPOINT`;
  `metrics_exporter=prometheus|otlp`.
- Logs now carry the active span's `trace_id` for log↔trace correlation.
- OTLP/Prometheus exporters remain optional behind the `[otlp]`/`[prometheus]`
  extras.

## [0.1.1] - 2026-06-01
- Added dual licensing guidance and documentation.
- Introduced internal release workflow improvements for package verification.
- Expanded supported Python versions to 3.10–3.14.
- Fixed Unicode-safe logging compatibility with Uvicorn formatters that reference
  `levelprefix`.

## [0.1.0] - 2025-01-01
- Initial release of wanAspects with logging/tracing/metrics aspects.
