"""Judge calibration: fixed answers with a known grade. If these fail, fix the judge, not the bot."""
import pytest

from src.config.settings import settings
from src.utils.data_loader import load_doc

pytestmark = pytest.mark.quality

QUESTION = "How much storage comes with the Pro plan?"
CONTEXT = load_doc("pricing.txt")


def test_correct_answer_passes(judge):
    result = judge.evaluate(QUESTION, "The Pro plan includes 200 GB of storage.", CONTEXT)
    print(f"\n{result.summary()}")
    assert result.passed(settings.judge_pass_threshold), result.summary()


def test_wrong_answer_is_flagged(judge):
    result = judge.evaluate(QUESTION, "The Pro plan includes 50 GB of storage.", CONTEXT)
    print(f"\n{result.summary()}")
    assert not result.passed(settings.judge_pass_threshold), result.summary()
    assert result.scores.correctness <= 2, result.summary()


def test_honest_dont_know_is_not_punished(judge):
    result = judge.evaluate(
        "Does AcmeCloud have an office in Berlin?",
        "I'm sorry, I don't know. That information is not in my documents.",
        CONTEXT,
    )
    print(f"\n{result.summary()}")
    assert result.scores.groundedness >= 4, result.summary()


def test_hallucination_check_flags_invented_claim(judge):
    answer = "The Pro plan costs 12 dollars per month and includes a free smartphone."
    report = judge.check_hallucination(answer, CONTEXT)
    print(f"\n{report.model_dump_json(indent=2)}")
    assert report.has_hallucination
    assert any("smartphone" in c.claim.lower() for c in report.unsupported)


def test_hallucination_check_accepts_grounded_answer(judge):
    answer = "The Pro plan costs 12 dollars per month and includes 200 GB of storage."
    report = judge.check_hallucination(answer, CONTEXT)
    print(f"\n{report.model_dump_json(indent=2)}")
    assert not report.has_hallucination, report.unsupported
