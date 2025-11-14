from __future__ import annotations

from datetime import datetime

from .config import load_config


def diag() -> None:
    cfg = load_config()
    print("wanaspects diagnostics")
    print("timestamp:", datetime.utcnow().isoformat() + "Z")
    print("enabled:", cfg.enabled)
    print("bundle:", cfg.bundle)
    print("trace_sampling:", cfg.trace_sampling)
    print("otlp_endpoint:", cfg.otlp_endpoint or "<none>")
    print("console_spans:", cfg.console_spans)
    print("log_level:", cfg.log_level, "log_json:", cfg.log_json)
    print("metrics_enabled:", cfg.metrics_enabled)
    print(
        "dev_peek_max_rows:",
        "<none>" if cfg.dev_peek_max_rows is None else cfg.dev_peek_max_rows,
    )
    print("boundary_allow:", ",".join(cfg.boundary_allow))


if __name__ == "__main__":
    diag()
