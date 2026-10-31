import pytest

from src.config.settings import settings
from src.evaluators.reference import fact_coverage, similarity
from src.models.testcase import ReferenceCase
from src.utils.data_loader import load_cases

pytestmark = pytest.mark.quality

CASES = load_cases("reference_cases.yaml", ReferenceCase)


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_answer_matches_reference(client, case: ReferenceCase):
    response = client.send(case.question)
    answer = response.answer

    facts = fact_coverage(answer, case.expected_facts)
    sim = similarity(answer, case.reference_answer)
    print(f"\n[{case.id}] fact_coverage={facts.score:.2f} {sim.detail}")

    failed = []
    if case.source not in response.sources:
        failed.append(f"source {case.source} not in {response.sources}")
    if facts.score < settings.min_fact_coverage:
        failed.append(f"fact coverage {facts.score:.2f}: {facts.detail}")
    if sim.score < settings.min_similarity:
        failed.append(f"{sim.detail} < {settings.min_similarity}")
    assert not failed, f"{failed}\nANSWER: {answer}"
