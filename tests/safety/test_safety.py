import pytest

from src.evaluators.rules import contains_none
from src.evaluators.safety import is_refusal
from src.models.testcase import SafetyCase
from src.utils.data_loader import load_cases

pytestmark = pytest.mark.safety

CASES = load_cases("safety.yaml", SafetyCase)


@pytest.mark.parametrize("case", CASES, ids=[f"{c.category}-{c.id}" for c in CASES])
def test_unsafe_request_is_declined(client, judge, case: SafetyCase):
    answer = client.send(case.prompt).answer

    if case.forbidden_words:
        leak = contains_none(answer, case.forbidden_words)
        assert leak, f"{leak.detail}\nANSWER: {answer}"

    refusal = is_refusal(answer)
    if refusal:
        print(f"\n[{case.id}] rules: {refusal.detail}")
        return

    # Rules are unsure (no refusal phrase): let the LLM judge decide this borderline answer.
    verdict = judge.check_safety(case.prompt, answer)
    print(f"\n[{case.id}] judge: refused={verdict.refused} harmful={verdict.harmful_content} "
          f"{verdict.reasoning}")
    assert verdict.safe, f"{verdict.reasoning}\nANSWER: {answer}"
