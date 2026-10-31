import pytest

from src.evaluators.reference import fact_coverage, keyword_coverage, similarity
from src.models.testcase import ReferenceCase

pytestmark = pytest.mark.unit

ANSWER = "The desktop app runs on Windows and Linux."


def test_fact_coverage_full_and_partial():
    assert fact_coverage(ANSWER, [["Windows"], ["Linux"]]).score == 1.0
    result = fact_coverage(ANSWER, [["Windows"], ["macOS"]])
    assert result.score == 0.5
    assert "macOS" in result.detail


def test_fact_coverage_accepts_any_variant():
    assert fact_coverage("Refunds within 14-day window", [["14 days", "14-day"]]).score == 1.0


def test_keyword_coverage():
    assert keyword_coverage(ANSWER, ["windows", "linux", "android", "ios"]).score == 0.5


def test_similarity_bounds():
    assert similarity(ANSWER, ANSWER).score == 1.0
    assert similarity(ANSWER, "Bananas are yellow.").score == 0.0


def test_similarity_ignores_case_and_punctuation():
    assert similarity("WINDOWS, Linux!", "windows linux").score == 1.0


def test_reference_case_wraps_plain_string_facts():
    case = ReferenceCase(
        id="x", question="q", source="a.txt", reference_answer="r",
        expected_facts=["Windows", ["macOS", "mac"]],
    )
    assert case.expected_facts == [["Windows"], ["macOS", "mac"]]
