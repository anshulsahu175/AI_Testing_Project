import json

import pytest

from src.evaluators.prompts import HALLUCINATION_PROMPT, JUDGE_PROMPT, SAFETY_PROMPT
from src.mocks.mock_bot import DONT_KNOW, mock_answer
from src.mocks.mock_judge import MockJudgeClient

pytestmark = pytest.mark.unit

CONTEXT = "The Pro plan costs 12 dollars per month and includes 200 GB of storage."


def test_mock_bot_canned_answer_ignores_case_and_spaces():
    assert "12" in mock_answer("  how much does the PRO plan cost? ", [])


def test_mock_bot_unknown_question_gets_dont_know():
    assert mock_answer("What is the capital of France?", []) == DONT_KNOW


def test_mock_bot_remembers_name_only_from_history():
    history = [{"role": "user", "content": "Hi, my name is Riya."},
               {"role": "assistant", "content": "Hello Riya."}]
    assert mock_answer("What is my name?", history) == "Your name is Riya."
    assert mock_answer("What is my name?", []) == DONT_KNOW


def _judge(answer: str) -> dict:
    prompt = JUDGE_PROMPT.format(question="q", answer=answer, context=CONTEXT)
    return json.loads(MockJudgeClient().generate(prompt))


def test_mock_judge_passes_grounded_answer_and_fails_wrong_number():
    assert _judge("The Pro plan includes 200 GB of storage.")["verdict"] == "pass"
    wrong = _judge("The Pro plan includes 50 GB of storage.")
    assert wrong["verdict"] == "fail" and wrong["scores"]["correctness"] == 1


def test_mock_judge_flags_invented_claim():
    prompt = HALLUCINATION_PROMPT.format(
        answer="The Pro plan costs 12 dollars and includes a free smartphone.", context=CONTEXT)
    claims = json.loads(MockJudgeClient().generate(prompt))["claims"]
    assert [c["claim"] for c in claims if not c["supported"]] == ["includes a free smartphone"]


def test_mock_judge_safety_uses_refusal_rules():
    prompt = SAFETY_PROMPT.format(request="r", answer="Sorry, I can't help with that.")
    assert json.loads(MockJudgeClient().generate(prompt))["refused"] is True
