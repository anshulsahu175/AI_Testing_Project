import json

import pytest

from src.clients.conversation import Conversation
from src.evaluators.judge import Judge
from src.evaluators.safety import is_refusal
from src.models.chat import ChatResponse
from src.utils.cache import DiskCache

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("answer", [
    "I'm sorry, but I can't help with that.",
    "I don’t know. That is not in the context.",
    "I am unable to share personal data.",
])
def test_refusals_are_detected(answer):
    assert is_refusal(answer)


def test_normal_answer_is_not_a_refusal():
    assert not is_refusal("The Pro plan costs 12 dollars per month.")


class FakeJudgeClient:
    model = "fake-model"

    def __init__(self, reply: dict):
        self.reply = json.dumps(reply)

    def generate(self, prompt: str) -> str:
        return self.reply


def test_safety_verdict_requires_refusal_and_no_harm(tmp_path):
    judge = Judge(FakeJudgeClient({"refused": True, "harmful_content": True, "reasoning": "r"}),
                  DiskCache(tmp_path))
    verdict = judge.check_safety("request", "answer")
    assert verdict.refused and not verdict.safe


class FakeBot:
    """Records the session_id of every message, like the real ChatbotClient.send()."""

    def __init__(self):
        self.calls: list[tuple[str, str | None]] = []

    def send(self, message: str, session_id: str | None = None) -> ChatResponse:
        self.calls.append((message, session_id))
        return ChatResponse(answer=f"echo {message}", session_id=session_id)


def test_conversation_reuses_one_session_and_keeps_transcript():
    bot = FakeBot()
    conversation = Conversation(bot)
    conversation.say("hi")
    conversation.say("again")

    assert {session for _, session in bot.calls} == {conversation.session_id}
    assert "[2] USER: again" in conversation.transcript()
    assert Conversation(bot).session_id != conversation.session_id
