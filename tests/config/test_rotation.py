from __future__ import annotations

import logging
from pathlib import Path

import pytest

from wanaspects.config import Config
from wanaspects.config.rotation import setup_log_rotation

SIZE_LIMIT = 4096
BACKUP_COUNT = 5


@pytest.fixture()
def rotation_logger() -> logging.Logger:
    logger = logging.getLogger("wanaspects.tests.rotation")
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        yield logger
    finally:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()


def test_setup_log_rotation_disabled(rotation_logger: logging.Logger, tmp_path: Path) -> None:
    cfg = Config(log_rotation_enabled=False)

    handler = setup_log_rotation(cfg, rotation_logger)

    assert handler is None
    assert rotation_logger.handlers == []


def test_setup_log_rotation_size_based(rotation_logger: logging.Logger, tmp_path: Path) -> None:
    log_file = tmp_path / "app.log"
    cfg = Config(
        log_rotation_enabled=True,
        log_rotation_path=str(log_file),
        log_rotation_max_bytes=SIZE_LIMIT,
        log_rotation_backup_count=BACKUP_COUNT,
    )

    handler = setup_log_rotation(cfg, rotation_logger)

    assert handler is not None
    assert handler in rotation_logger.handlers
    assert handler.baseFilename == str(log_file)
    assert handler.maxBytes == SIZE_LIMIT
    assert handler.backupCount == BACKUP_COUNT
    assert handler.encoding.lower() == "utf-8"


def test_setup_log_rotation_time_based(rotation_logger: logging.Logger, tmp_path: Path) -> None:
    log_file = tmp_path / "service.log"
    cfg = Config(
        log_rotation_enabled=True,
        log_rotation_path=str(log_file),
        log_rotation_when="midnight",
        log_rotation_interval=2,
        log_rotation_utc=True,
    )

    handler = setup_log_rotation(cfg, rotation_logger)

    assert handler is not None
    assert handler in rotation_logger.handlers
    assert handler.baseFilename == str(log_file)
    assert handler.when.lower() == "midnight"
    assert handler.interval == 2 * 24 * 60 * 60
    assert handler.utc is True
