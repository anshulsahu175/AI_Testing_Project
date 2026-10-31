import pytest

from src.evaluators.rules import (
    contains_all,
    contains_any,
    contains_none,
    is_valid_json,
    length_between,
    matches_regex,
)

pytestmark = pytest.mark.unit

TEXT = "The Pro plan costs 12 dollars per month."


def test_contains_any():
    assert contains_any(TEXT, ["99", "12"])
    assert not contains_any(TEXT, ["99", "40"])


def test_contains_any_ignores_case():
    assert contains_any(TEXT, ["PRO PLAN"])


def test_contains_any_handles_unicode_spaces_and_quotes():
    assert contains_any("The Free plan includes 5 GB.", ["5 GB"])
    assert contains_any("I don’t know.", ["don't know"])


def test_contains_all():
    assert contains_all(TEXT, ["pro", "12"])
    result = contains_all(TEXT, ["pro", "40"])
    assert not result
    assert "40" in result.detail


def test_contains_none():
    assert contains_none(TEXT, ["Paris"])
    assert not contains_none(TEXT, ["dollars"])


def test_matches_regex():
    assert matches_regex(TEXT, r"\d+ dollars")
    assert not matches_regex(TEXT, r"\d+ euros")


def test_length_between():
    assert length_between(TEXT, 1, 100)
    assert not length_between("   ", 1, 100)
    assert not length_between(TEXT, 1, 5)


def test_is_valid_json():
    assert is_valid_json('{"a": 1}')
    assert not is_valid_json("{a: 1}")
