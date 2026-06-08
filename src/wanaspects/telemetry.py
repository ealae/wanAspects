from __future__ import annotations

import logging
import os
from typing import Any

from .config import Config, load_config
from .config.rotation import setup_log_rotation
from .filters import RedactionFilter
from .formatters import UnicodeSafeFormatter

# Metrics and logs rely on process-global providers, so initialization must be
# idempotent: OpenTelemetry forbids overriding the provider and binding a
# Prometheus scrape port twice would raise "address already in use". Held in
# mutable dicts so callers can reset them in tests without the `global` statement.
_METRICS_STATE = {"initialized": False}
_LOGS_STATE = {"initialized": False}

# File handles for the `file` exporters, kept alive for the process lifetime.
_OPEN_FILES: list[Any] = []


def _open_telemetry_file(cfg: Config, signal: str) -> Any:
    """Open an append-mode JSONL file for a signal under ``telemetry_dir``.

    Named ``<service>.<pid>.<signal>.jsonl`` so several services — and several
    processes of the same service — can share one directory without clobbering
    each other's lines. This is the air-gapped, no-collector path: the SDK
    writes the files in-process, no external binary required.
    """
    base_dir = cfg.telemetry_dir or "."
    os.makedirs(base_dir, exist_ok=True)
    service = os.getenv("SERVICE_NAME", "wanaspects")
    path = os.path.join(base_dir, f"{service}.{os.getpid()}.{signal}.jsonl")
    handle = open(path, "a", encoding="utf-8")  # noqa: SIM115 - lives for process lifetime
    _OPEN_FILES.append(handle)
    return handle


def _otlp_endpoint_for(base: str, signal: str) -> str:
    """Resolve a per-signal OTLP/HTTP URL from a base endpoint.

    The HTTP exporters POST to ``/v1/<signal>``. Unlike ``OTEL_EXPORTER_OTLP_*``
    env vars, an explicit ``endpoint=`` is used verbatim, so a base URL like
    ``http://127.0.0.1:4318`` must get the signal path appended; a URL that
    already carries a ``/v1/...`` path is left untouched.
    """
    trimmed = base.rstrip("/")
    if "/v1/" in trimmed:
        return trimmed
    if trimmed.endswith("/v1"):
        return f"{trimmed}/{signal}"
    return f"{trimmed}/v1/{signal}"


def _try_init_structlog(cfg: Config) -> None:
    try:  # pragma: no cover - environment dependent
        import structlog  # noqa: PLC0415

        processors: list[Any] = [
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
        ]
        if cfg.log_json:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.processors.KeyValueRenderer())
        structlog.configure(processors=processors)
    except Exception:
        # Structlog not installed or misconfigured — skip silently.
        pass


def _try_init_tracing(cfg: Config) -> None:
    try:  # pragma: no cover - environment dependent
        from opentelemetry import trace  # noqa: PLC0415
        from opentelemetry.sdk.resources import Resource  # noqa: PLC0415
        from opentelemetry.sdk.trace import TracerProvider  # noqa: PLC0415
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # noqa: PLC0415
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased  # noqa: PLC0415

        provider = TracerProvider(
            sampler=TraceIdRatioBased(cfg.trace_sampling),
            resource=Resource.create({"service.name": os.getenv("SERVICE_NAME", "wanaspects")}),
        )

        # Resolve the exporter: explicit `traces_exporter` wins, else fall back
        # to legacy behaviour (OTLP when an endpoint is set, else console).
        exporter_kind = (cfg.traces_exporter or "none").lower()
        if exporter_kind == "none":
            if cfg.otlp_endpoint:
                exporter_kind = "otlp"
            elif cfg.console_spans:
                exporter_kind = "console"

        if exporter_kind == "otlp" and cfg.otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # noqa: PLC0415
                    OTLPSpanExporter,
                )

                span_endpoint = _otlp_endpoint_for(cfg.otlp_endpoint, "traces")
                exporter = OTLPSpanExporter(endpoint=span_endpoint)
                provider.add_span_processor(BatchSpanProcessor(exporter))
            except Exception:
                # Exporter not available — keep provider without exporter
                pass
        elif exporter_kind == "file":
            # In-process JSONL file — no collector/binary, works air-gapped.
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter  # noqa: PLC0415

            span_file = _open_telemetry_file(cfg, "traces")
            provider.add_span_processor(
                BatchSpanProcessor(
                    ConsoleSpanExporter(
                        out=span_file, formatter=lambda span: span.to_json(indent=None) + "\n"
                    )
                )
            )
        elif exporter_kind == "console":
            try:
                from opentelemetry.sdk.trace.export import (  # noqa: PLC0415
                    ConsoleSpanExporter,
                    SimpleSpanProcessor,
                )

                provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
            except Exception:
                pass

        trace.set_tracer_provider(provider)
    except Exception:
        # OpenTelemetry not installed — skip silently.
        pass


def _configure_redaction(cfg: Config) -> None:
    root_logger = logging.getLogger()
    for existing in list(root_logger.filters):
        if isinstance(existing, RedactionFilter):
            root_logger.removeFilter(existing)
    if not cfg.enable_redaction:
        return
    root_logger.addFilter(RedactionFilter(cfg.redact_keys))


def _configure_unicode(cfg: Config) -> None:
    if not cfg.unicode_safe:
        return
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if not isinstance(handler, logging.StreamHandler):
            continue
        existing = handler.formatter
        if isinstance(existing, UnicodeSafeFormatter):
            continue
        fmt = getattr(existing, "_style", None)
        if fmt is not None and hasattr(fmt, "_fmt"):
            format_string = fmt._fmt
        elif existing is not None:
            format_string = existing._fmt if hasattr(existing, "_fmt") else None
        else:
            format_string = None
        datefmt = getattr(existing, "datefmt", None) if existing else None
        style_char = "%"
        if existing is not None:
            style_obj = getattr(existing, "_style", None)
            if style_obj is not None:
                from logging import StrFormatStyle, StringTemplateStyle  # noqa: PLC0415

                if isinstance(style_obj, StrFormatStyle):
                    style_char = "{"
                elif isinstance(style_obj, StringTemplateStyle):
                    style_char = "$"
        encoding = getattr(getattr(handler, "stream", None), "encoding", None)
        handler.setFormatter(
            UnicodeSafeFormatter(
                format_string,
                datefmt=datefmt,
                style=style_char,
                encoding=encoding,
                strip_emoji=cfg.strip_emoji,
            )
        )


def _configure_rotation(cfg: Config) -> None:
    if not cfg.log_rotation_enabled:
        return
    setup_log_rotation(cfg, logging.getLogger())


def _try_init_metrics(cfg: Config) -> None:
    """Install a global MeterProvider so the metrics aspect's instruments export.

    Without this the aspect's counters/histograms bind to the no-op default
    provider and never reach Prometheus. Selects an exporter via
    ``WANCHAIN_METRICS_EXPORTER``:

    - ``prometheus``: register a :class:`PrometheusMetricReader` (scraped at
      ``/metrics`` by the host, or via a standalone HTTP server when
      ``WANCHAIN_METRICS_PORT`` is set for non-ASGI services).
    - ``otlp``: push to a collector via ``WANCHAIN_OTLP_ENDPOINT``.
    """
    if _METRICS_STATE["initialized"] or not cfg.metrics_enabled:
        return
    exporter = (cfg.metrics_exporter or "none").lower()
    if exporter not in {"prometheus", "otlp"}:
        return
    try:  # pragma: no cover - environment dependent
        from opentelemetry import metrics  # noqa: PLC0415
        from opentelemetry.sdk.metrics import MeterProvider  # noqa: PLC0415
        from opentelemetry.sdk.resources import Resource  # noqa: PLC0415

        resource = Resource.create({"service.name": os.getenv("SERVICE_NAME", "wanaspects")})
        readers: list[Any] = []

        if exporter == "prometheus":
            from opentelemetry.exporter.prometheus import (  # noqa: PLC0415
                PrometheusMetricReader,
            )

            readers.append(PrometheusMetricReader())
            if cfg.metrics_port:
                from prometheus_client import start_http_server  # noqa: PLC0415

                start_http_server(cfg.metrics_port)
        else:  # otlp
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import (  # noqa: PLC0415
                OTLPMetricExporter,
            )
            from opentelemetry.sdk.metrics.export import (  # noqa: PLC0415
                PeriodicExportingMetricReader,
            )

            otlp_exporter = (
                OTLPMetricExporter(endpoint=cfg.otlp_endpoint)
                if cfg.otlp_endpoint
                else OTLPMetricExporter()
            )
            readers.append(PeriodicExportingMetricReader(otlp_exporter))

        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=readers))
        _METRICS_STATE["initialized"] = True
    except Exception:
        # Exporter not installed (optional extra) or misconfigured — skip silently.
        return


def _try_init_logs(cfg: Config) -> None:
    """Bridge stdlib ``logging`` to OpenTelemetry so logs are centralized.

    The logging aspect (and every ``logging.getLogger(__name__)`` across the
    services) already emits stdlib records, so attaching an OpenTelemetry
    :class:`LoggingHandler` to the root logger forwards them — with the active
    span's ``trace_id``/``span_id`` attached automatically. Selected via
    ``WANCHAIN_LOGS_EXPORTER``:

    - ``otlp``: push to a collector at ``WANCHAIN_OTLP_ENDPOINT``.
    - ``file``: write JSONL to ``WANCHAIN_TELEMETRY_DIR`` in-process — no
      collector or binary, works on an air-gapped host.
    """
    exporter_kind = (cfg.logs_exporter or "none").lower()
    if _LOGS_STATE["initialized"] or exporter_kind not in {"otlp", "file"}:
        return
    if exporter_kind == "otlp" and not cfg.otlp_endpoint:
        return
    try:  # pragma: no cover - environment dependent
        from opentelemetry._logs import set_logger_provider  # noqa: PLC0415
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler  # noqa: PLC0415
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor  # noqa: PLC0415
        from opentelemetry.sdk.resources import Resource  # noqa: PLC0415

        if exporter_kind == "file":
            from opentelemetry.sdk._logs.export import ConsoleLogExporter  # noqa: PLC0415

            log_exporter: Any = ConsoleLogExporter(
                out=_open_telemetry_file(cfg, "logs"),
                formatter=lambda record: record.to_json(indent=None) + "\n",
            )
        else:  # otlp — requires the optional `otlp` extra
            from opentelemetry.exporter.otlp.proto.http._log_exporter import (  # noqa: PLC0415
                OTLPLogExporter,
            )

            endpoint = cfg.otlp_endpoint
            assert endpoint is not None  # guarded above for the otlp path
            log_exporter = OTLPLogExporter(endpoint=_otlp_endpoint_for(endpoint, "logs"))

        resource = Resource.create({"service.name": os.getenv("SERVICE_NAME", "wanaspects")})
        provider = LoggerProvider(resource=resource)
        provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        set_logger_provider(provider)

        level = getattr(logging, cfg.log_level.upper(), logging.INFO)
        root = logging.getLogger()
        # The root logger filters by level *before* handlers run, so records
        # below its level (default WARNING) never reach the OTLP handler. Lower
        # it to the configured level — but never raise it, to avoid suppressing
        # a more verbose level the host already set.
        if root.level == logging.NOTSET or root.level > level:
            root.setLevel(level)
        handler = LoggingHandler(level=level, logger_provider=provider)
        root.addHandler(handler)
        _LOGS_STATE["initialized"] = True
    except Exception:
        # OTLP log exporter not installed (optional extra) or misconfigured.
        return


def init_telemetry() -> None:
    """Initialize structlog and OpenTelemetry.

    Safe to call multiple times. No-op if optional deps are not installed.
    """
    cfg = load_config()
    _configure_redaction(cfg)
    _configure_unicode(cfg)
    _configure_rotation(cfg)
    if not cfg.enabled:
        return
    _try_init_structlog(cfg)
    _try_init_tracing(cfg)
    _try_init_metrics(cfg)
    _try_init_logs(cfg)
