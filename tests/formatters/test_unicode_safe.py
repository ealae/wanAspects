import logging

import pytest

from wanaspects.formatters.unicode_safe import UnicodeSafeFormatter


def make_record(message: str) -> logging.LogRecord:
    return logging.LogRecord("test", logging.INFO, __file__, 10, message, (), None)


def test_utf8_pass_through() -> None:
    formatter = UnicodeSafeFormatter("%(message)s", encoding="utf-8")
    record = make_record("Cache hit ✅ for user François")

    formatted = formatter.format(record)

    assert formatted == "Cache hit ✅ for user François"


@pytest.mark.parametrize("strip", [True, None])
def test_non_utf8_strips_emoji_and_invalid_chars(strip: bool | None) -> None:
    formatter = UnicodeSafeFormatter(
        "%(message)s",
        encoding="cp1252",
        strip_emoji=strip,
        emoji_replacement="OK",
    )
    record = make_record("Cache hit ✅ for user François ✨")

    formatted = formatter.format(record)

    assert formatted == "Cache hit OK for user François OK"


def test_force_replace_when_not_stripping() -> None:
    formatter = UnicodeSafeFormatter(
        "%(message)s",
        encoding="cp1252",
        strip_emoji=False,
        replacement="?",
    )
    record = make_record("Cache hit ✅")

    formatted = formatter.format(record)

    assert formatted == "Cache hit ?"
