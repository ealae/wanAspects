"""Utilities for configuring file-based log rotation."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

from . import Config

__all__ = ["setup_log_rotation"]


def _remove_existing(logger: logging.Logger, target: Path) -> None:
    for handler in list(logger.handlers):
        base = getattr(handler, "baseFilename", None)
        if base and Path(base) == target:
            logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:  # pragma: no cover - defensive
                pass


def setup_log_rotation(
    cfg: Config,
    logger: logging.Logger | None = None,
) -> logging.Handler | None:
    """Attach a rotating file handler based on configuration."""

    if not cfg.log_rotation_enabled:
        return None

    path_value = cfg.log_rotation_path or "logs/wanaspects.log"
    log_path = Path(path_value)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    target_logger = logger or logging.getLogger()
    _remove_existing(target_logger, log_path)

    encoding = "utf-8"
    handler: logging.Handler

    if cfg.log_rotation_when:
        handler = TimedRotatingFileHandler(
            filename=str(log_path),
            when=str(cfg.log_rotation_when),
            interval=max(cfg.log_rotation_interval, 1),
            backupCount=max(cfg.log_rotation_backup_count, 0),
            encoding=encoding,
            utc=cfg.log_rotation_utc,
        )
    else:
        handler = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max(cfg.log_rotation_max_bytes, 1024),
            backupCount=max(cfg.log_rotation_backup_count, 0),
            encoding=encoding,
        )

    target_logger.addHandler(handler)
    return handler
