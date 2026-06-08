import logging
from types import SimpleNamespace

import pytest

from wanaspects.filters.redaction import RedactionFilter


@pytest.fixture()
def record_factory():
    def _factory(msg, **kwargs):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg=msg,
            args=kwargs.pop("args", ()),
            exc_info=None,
        )
        for key, value in kwargs.items():
            setattr(record, key, value)
        return record

    return _factory


def test_default_keys_are_redacted(record_factory):
    record = record_factory("password=hunter2 token=abcd1234")

    redactor = RedactionFilter()
    assert redactor.filter(record) is True
    assert record.msg == "password=<REDACTED> token=<REDACTED>"


def test_case_insensitive_match(record_factory):
    record = record_factory("API_KEY=abcd SECRET=top")

    redactor = RedactionFilter()
    redactor.filter(record)

    assert record.msg == "API_KEY=<REDACTED> SECRET=<REDACTED>"


def test_additional_keys_can_be_supplied(record_factory):
    record = record_factory("session_id=1234")

    redactor = RedactionFilter({"session_id"})
    redactor.filter(record)

    assert record.msg == "session_id=<REDACTED>"


def test_structured_data_is_redacted_deeply(record_factory):
    record = record_factory(
        {"user": {"password": "secret", "profile": {"token": "abc"}}, "items": [{"api_key": "key"}]}
    )

    redactor = RedactionFilter()
    redactor.filter(record)

    assert record.msg == {
        "user": {"password": "<REDACTED>", "profile": {"token": "<REDACTED>"}},
        "items": [{"api_key": "<REDACTED>"}],
    }


def test_dict_args_are_redacted(record_factory):
    record = record_factory("User login", args={"token": "abc", "other": "value"})

    redactor = RedactionFilter()
    redactor.filter(record)

    assert record.args == {"token": "<REDACTED>", "other": "value"}


def test_extra_attributes_are_redacted(record_factory):
    record = record_factory("User login", sensitive="token=abc", context={"password": "secret"})

    redactor = RedactionFilter()
    redactor.filter(record)

    assert record.sensitive == "token=<REDACTED>"
    assert record.context == {"password": "<REDACTED>"}


@pytest.mark.parametrize(
    "message,expected",
    [
        ("authorization: Bearer abc", "authorization: <REDACTED>"),
        ("token 'abc'", "token '<REDACTED>'"),
        ("password=abc, keep", "password=<REDACTED>, keep"),
        ("nested token=abc", "nested token=<REDACTED>"),
    ],
)
def test_varied_patterns_are_redacted(record_factory, message, expected):
    record = record_factory(message)

    redactor = RedactionFilter()
    redactor.filter(record)

    assert record.msg == expected


@pytest.mark.parametrize(
    "value",
    [None, 123, 12.5, True, False, SimpleNamespace(token="abc")],
)
def test_non_string_values_are_left_unmodified(value, record_factory):
    record = record_factory(value)

    redactor = RedactionFilter()
    redactor.filter(record)

    assert record.msg is value
