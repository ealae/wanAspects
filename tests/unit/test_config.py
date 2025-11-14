from wanaspects.config import load_config

TRACE_SAMPLING_OVERRIDE = 0.25
DEV_PEEK_OVERRIDE = 42
DEV_PEEK_DISK = 10
MAX_BYTES_OVERRIDE = 1024
BACKUP_COUNT_OVERRIDE = 7
ROTATION_INTERVAL_OVERRIDE = 12
DISK_MAX_BYTES = 2048
DISK_BACKUP_COUNT = 3


def test_load_config_env_overrides(tmp_path, monkeypatch) -> None:  # noqa: PLR0915
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.wanchain.aspects]
enabled = false
bundle = "prod"
trace_sampling = 0.0
metrics_enabled = false
dev_peek_max_rows = 10
boundary_allow = ["geo"]
enable_redaction = false
redact_keys = ["license"]
unicode_safe = true
strip_emoji = false
force_utf8 = false
log_rotation_enabled = true
log_rotation_path = "logs/app.log"
log_rotation_max_bytes = 2048
log_rotation_backup_count = 3
log_rotation_when = "midnight"
log_rotation_interval = 1
log_rotation_utc = true
"""
    )

    monkeypatch.setenv("WANCHAIN_ASPECTS_ENABLED", "true")
    monkeypatch.setenv("WANCHAIN_TRACE_SAMPLING", str(TRACE_SAMPLING_OVERRIDE))
    monkeypatch.setenv("WANCHAIN_METRICS_ENABLED", "true")
    monkeypatch.setenv("WANCHAIN_DEV_PEEK_MAX_ROWS", str(DEV_PEEK_OVERRIDE))
    monkeypatch.setenv("WANCHAIN_BOUNDARY_ALLOW", "geo,io")
    monkeypatch.setenv("WANCHAIN_ENABLE_REDACTION", "true")
    monkeypatch.setenv("WANCHAIN_REDACT_KEYS", "session_id,token")
    monkeypatch.setenv("WANCHAIN_UNICODE_SAFE", "false")
    monkeypatch.setenv("WANCHAIN_STRIP_EMOJI", "true")
    monkeypatch.setenv("WANCHAIN_FORCE_UTF8", "true")
    monkeypatch.setenv("WANCHAIN_LOG_ROTATION_ENABLED", "true")
    monkeypatch.setenv("WANCHAIN_LOG_ROTATION_PATH", "logs/runtime.log")
    monkeypatch.setenv("WANCHAIN_LOG_ROTATION_MAX_BYTES", str(MAX_BYTES_OVERRIDE))
    monkeypatch.setenv("WANCHAIN_LOG_ROTATION_BACKUP_COUNT", str(BACKUP_COUNT_OVERRIDE))
    monkeypatch.setenv("WANCHAIN_LOG_ROTATION_WHEN", "H")
    monkeypatch.setenv("WANCHAIN_LOG_ROTATION_INTERVAL", str(ROTATION_INTERVAL_OVERRIDE))
    monkeypatch.setenv("WANCHAIN_LOG_ROTATION_UTC", "false")

    cfg = load_config(str(pyproject))
    assert cfg.enabled is True
    assert cfg.bundle == "prod"
    assert cfg.trace_sampling == TRACE_SAMPLING_OVERRIDE
    assert cfg.metrics_enabled is True
    assert cfg.dev_peek_max_rows == DEV_PEEK_OVERRIDE
    assert cfg.boundary_allow == ("geo", "io")
    assert cfg.enable_redaction is True
    assert cfg.redact_keys == ("session_id", "token")
    assert cfg.unicode_safe is False
    assert cfg.strip_emoji is True
    assert cfg.force_utf8 is True
    assert cfg.log_rotation_enabled is True
    assert cfg.log_rotation_path == "logs/runtime.log"
    assert cfg.log_rotation_max_bytes == MAX_BYTES_OVERRIDE
    assert cfg.log_rotation_backup_count == BACKUP_COUNT_OVERRIDE
    assert cfg.log_rotation_when == "H"
    assert cfg.log_rotation_interval == ROTATION_INTERVAL_OVERRIDE
    assert cfg.log_rotation_utc is False

    monkeypatch.delenv("WANCHAIN_ASPECTS_ENABLED")
    monkeypatch.delenv("WANCHAIN_TRACE_SAMPLING")
    monkeypatch.delenv("WANCHAIN_METRICS_ENABLED")
    monkeypatch.delenv("WANCHAIN_DEV_PEEK_MAX_ROWS")
    monkeypatch.delenv("WANCHAIN_BOUNDARY_ALLOW")
    monkeypatch.delenv("WANCHAIN_ENABLE_REDACTION")
    monkeypatch.delenv("WANCHAIN_REDACT_KEYS")
    monkeypatch.delenv("WANCHAIN_UNICODE_SAFE")
    monkeypatch.delenv("WANCHAIN_STRIP_EMOJI")
    monkeypatch.delenv("WANCHAIN_FORCE_UTF8")
    monkeypatch.delenv("WANCHAIN_LOG_ROTATION_ENABLED")
    monkeypatch.delenv("WANCHAIN_LOG_ROTATION_PATH")
    monkeypatch.delenv("WANCHAIN_LOG_ROTATION_MAX_BYTES")
    monkeypatch.delenv("WANCHAIN_LOG_ROTATION_BACKUP_COUNT")
    monkeypatch.delenv("WANCHAIN_LOG_ROTATION_WHEN")
    monkeypatch.delenv("WANCHAIN_LOG_ROTATION_INTERVAL")
    monkeypatch.delenv("WANCHAIN_LOG_ROTATION_UTC")

    cfg_disk = load_config(str(pyproject))
    assert cfg_disk.enabled is False
    assert cfg_disk.metrics_enabled is False
    assert cfg_disk.dev_peek_max_rows == DEV_PEEK_DISK
    assert cfg_disk.boundary_allow == ("geo",)
    assert cfg_disk.enable_redaction is False
    assert cfg_disk.redact_keys == ("license",)
    assert cfg_disk.unicode_safe is True
    assert cfg_disk.strip_emoji is False
    assert cfg_disk.force_utf8 is False
    assert cfg_disk.log_rotation_enabled is True
    assert cfg_disk.log_rotation_path == "logs/app.log"
    assert cfg_disk.log_rotation_max_bytes == DISK_MAX_BYTES
    assert cfg_disk.log_rotation_backup_count == DISK_BACKUP_COUNT
    assert cfg_disk.log_rotation_when == "midnight"
    assert cfg_disk.log_rotation_interval == 1
    assert cfg_disk.log_rotation_utc is True
