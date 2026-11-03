"""Prompt injection suite. A failing test is a FINDING about the bot, not a framework bug."""
import pytest

from src.evaluators.rules import contains_any, contains_none
from src.models.testcase import InjectionCase
from src.utils.data_loader import load_cases

pytestmark = pytest.mark.safety

CASES = load_cases("injection.yaml", InjectionCase)


def _param(case: InjectionCase):
    """Known findings run as xfail (not strict: LLM output varies, an attack may fail by luck)."""
    marks = []
    if case.known_issue:
        marks.append(pytest.mark.xfail(reason=f"{case.known_issue}, see FINDINGS.md", strict=False))
    return pytest.param(case, id=f"{case.category}-{case.id}", marks=marks)


@pytest.mark.parametrize("case", [_param(c) for c in CASES])
def test_injection_is_resisted(client, case: InjectionCase):
    answer = client.send(case.prompt).answer

    checks = [contains_none(answer, case.forbidden_words)]
    if case.expected_keywords:
        checks.append(contains_any(answer, case.expected_keywords))

    failed = [c.detail for c in checks if not c]
    assert not failed, f"attack worked ({case.category}): {failed}\nANSWER: {answer}"
