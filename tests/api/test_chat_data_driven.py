import pytest

from src.evaluators.rules import (
    contains_all,
    contains_any,
    contains_none,
    length_between,
    matches_regex,
)
from src.models.testcase import ApiCase
from src.utils.data_loader import load_cases

pytestmark = pytest.mark.api

CASES = load_cases("api_cases.yaml", ApiCase)


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_chat_case(client, case: ApiCase):
    answer = client.send(case.question).answer

    checks = [length_between(answer, max_len=case.max_length)]
    if case.expected_keywords:
        keyword_check = contains_all if case.match == "all" else contains_any
        checks.append(keyword_check(answer, case.expected_keywords))
    if case.forbidden_words:
        checks.append(contains_none(answer, case.forbidden_words))
    if case.regex:
        checks.append(matches_regex(answer, case.regex))

    failed = [c.detail for c in checks if not c]
    assert not failed, f"{failed}\nANSWER: {answer}"
