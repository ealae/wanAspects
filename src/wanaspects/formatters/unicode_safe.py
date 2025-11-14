"""Unicode-safe logging formatter for cross-platform consoles."""

from __future__ import annotations

import logging
import unicodedata
from typing import Any

__all__ = ["UnicodeSafeFormatter"]

EMOJI_RANGES: tuple[tuple[int, int], ...] = (
    (0x1F000, 0x1FAFF),
    (0x1F300, 0x1F5FF),
    (0x1F900, 0x1F9FF),
    (0x2600, 0x27BF),
    (0xFE00, 0xFE0F),
)


class UnicodeSafeFormatter(logging.Formatter):
    """Formatter that degrades gracefully when the target stream is not UTF-8."""

    def __init__(  # noqa: PLR0913
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: str = "%",
        *,
        encoding: str | None = None,
        strip_emoji: bool | None = None,
        emoji_replacement: str = "OK",
        replacement: str = "?",
    ) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.encoding = (encoding or "utf-8").lower()
        self._strip_emoji_setting = strip_emoji
        self.emoji_replacement = emoji_replacement
        self.replacement = replacement

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        """Format the record and sanitize unencodable characters."""

        formatted = super().format(record)
        sanitized = self._sanitize(formatted)
        if record.exc_text:
            record.exc_text = self._sanitize(record.exc_text)
        if record.stack_info:
            record.stack_info = self._sanitize(record.stack_info)
        return sanitized

    # Internal helpers -------------------------------------------------
    def _sanitize(self, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        if not value or self.encoding == "utf-8":
            return value
        sanitized = self._strip_unencodable(value)
        try:
            sanitized.encode(self.encoding)
        except UnicodeEncodeError:
            sanitized = sanitized.encode(self.encoding, errors="replace").decode(
                self.encoding,
                errors="ignore",
            )
        return sanitized

    def _strip_unencodable(self, text: str) -> str:
        should_strip_emoji = self._should_strip_emoji()
        result: list[str] = []
        for char in text:
            if should_strip_emoji and self._is_emoji(char):
                if self.emoji_replacement:
                    result.append(self.emoji_replacement)
                continue
            try:
                char.encode(self.encoding)
            except UnicodeEncodeError:
                result.append(self.replacement)
            else:
                result.append(char)
        return "".join(result)

    def _should_strip_emoji(self) -> bool:
        if self._strip_emoji_setting is None:
            return self.encoding != "utf-8"
        return self._strip_emoji_setting

    @staticmethod
    def _is_emoji(char: str) -> bool:
        if not char:
            return False
        codepoint = ord(char)
        for lower, upper in EMOJI_RANGES:
            if lower <= codepoint <= upper:
                return True
        try:
            name = unicodedata.name(char)
        except ValueError:
            return False
        return "EMOJI" in name or unicodedata.category(char) == "So"
