from __future__ import annotations

import logging
import os
from typing import Any

from .config import Config, load_config
from .config.rotation import setup_log_rotation
from .filters import RedactionFilter
from .formatters import UnicodeSafeFormatter


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

        # Optional OTLP exporter (install separately)
        endpoint = cfg.otlp_endpoint
        if endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # noqa: PLC0415
                    OTLPSpanExporter,
                )

                exporter = OTLPSpanExporter(endpoint=endpoint)
                provider.add_span_processor(BatchSpanProcessor(exporter))
            except Exception:
                # Exporter not available — keep provider without exporter
                pass
        # Optional console export for demos
        elif cfg.console_spans:
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
