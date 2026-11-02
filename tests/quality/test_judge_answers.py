import pytest

from src.config.settings import settings
from src.models.testcase import ReferenceCase
from src.utils.data_loader import load_cases, load_doc

pytestmark = pytest.mark.quality

CASES = load_cases("reference_cases.yaml", ReferenceCase)


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_bot_answer_judged(client, judge, case: ReferenceCase):
    answer = client.send(case.question).answer
    context = load_doc(case.source)

    result = judge.evaluate(case.question, answer, context)
    report = judge.check_hallucination(answer, context)
    print(f"\n[{case.id}] {result.summary()}\nunsupported: {[c.claim for c in report.unsupported]}")

    failed = []
    if not result.passed(settings.judge_pass_threshold):
        failed.append(f"judge avg {result.average:.2f} < {settings.judge_pass_threshold} "
                      f"or verdict {result.verdict}")
    if report.has_hallucination:
        failed.append(f"unsupported claims: {[c.claim for c in report.unsupported]}")
    assert not failed, f"{failed}\n{result.summary()}\nANSWER: {answer}"
