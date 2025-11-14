"""Sensitive data redaction for logging records."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable, Mapping
from typing import Any

__all__ = ["RedactionFilter"]


class RedactionFilter(logging.Filter):
    """Redact sensitive data in log records."""

    DEFAULT_KEYS: frozenset[str] = frozenset(
        {
            "api_key",
            "apikey",
            "auth",
            "authorization",
            "bearer",
            "credential",
            "password",
            "secret",
            "token",
        }
    )

    _SKIP_ATTRS = {
        "args",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def __init__(
        self,
        additional_keys: Iterable[str] | None = None,
        placeholder: str = "<REDACTED>",
    ) -> None:
        super().__init__()
        keys = {k.casefold() for k in self.DEFAULT_KEYS}
        if additional_keys:
            keys.update(k.casefold() for k in additional_keys)
        self._keys = frozenset(keys)
        self.placeholder = placeholder
        key_group = "|".join(sorted(re.escape(k) for k in self._keys))
        if key_group:
            self._string_patterns = (
                re.compile(
                    rf"(?P<key>{key_group})(?P<sep>\s*=\s*)(?P<quote>[\"']?)(?P<value>[^\s,'\"]+)(?P=quote)",
                    re.IGNORECASE,
                ),
                re.compile(
                    rf"(?P<key>{key_group})(?P<sep>\s*:\s*)(?P<value>[^,;\n]+)",
                    re.IGNORECASE,
                ),
                re.compile(
                    rf"(?P<key>{key_group})(?P<sep>\s+)(?P<quote>[\"'])(?P<value>[^\"']*)(?P=quote)",
                    re.IGNORECASE,
                ),
            )
        else:
            self._string_patterns = tuple()

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        """Apply redaction to the provided record."""

        record.msg = self._redact_object(record.msg)
        record.args = self._redact_args(record.args)

        for attr, value in list(record.__dict__.items()):
            if attr in self._SKIP_ATTRS:
                continue
            redacted = self._redact_object(value)
            if redacted is not value:
                setattr(record, attr, redacted)
        return True

    def _is_sensitive_key(self, key: Any) -> bool:
        return isinstance(key, str) and key.casefold() in self._keys

    def _redact_args(self, args: Any) -> Any:
        if isinstance(args, Mapping):
            return self._redact_mapping(args)
        if isinstance(args, tuple):
            return tuple(self._redact_object(arg) for arg in args)
        if isinstance(args, list):
            return [self._redact_object(arg) for arg in args]
        return args

    def _redact_object(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._redact_string(value)
        if isinstance(value, Mapping):
            return self._redact_mapping(value)
        if isinstance(value, list):
            return [self._redact_object(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self._redact_object(item) for item in value)
        if isinstance(value, set):
            return {self._redact_object(item) for item in value}
        return value

    def _redact_mapping(self, mapping: Mapping[Any, Any]) -> dict[Any, Any]:
        redacted: dict[Any, Any] = {}
        for key, value in mapping.items():
            if self._is_sensitive_key(key):
                redacted[key] = self.placeholder
            else:
                redacted[key] = self._redact_object(value)
        return redacted

    def _redact_string(self, text: str) -> str:
        if not self._string_patterns:
            return text
        redacted = text
        for pattern in self._string_patterns:
            redacted = pattern.sub(self._replace_match, redacted)
        return redacted

    def _replace_match(self, match: re.Match[str]) -> str:
        key = match.group("key")
        sep = match.group("sep") or ""
        quote = match.groupdict().get("quote", "")
        return f"{key}{sep}{quote}{self.placeholder}{quote}"
