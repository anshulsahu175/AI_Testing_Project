import pytest

from src.clients.conversation import Conversation
from src.evaluators.rules import contains_any, contains_none
from src.models.testcase import ConversationCase
from src.utils.data_loader import load_cases

pytestmark = pytest.mark.multi_turn

CASES = load_cases("multi_turn.yaml", ConversationCase)


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_conversation(client, case: ConversationCase):
    conversation = Conversation(client)

    failed = []
    for number, turn in enumerate(case.turns, 1):
        answer = conversation.say(turn.say)
        if turn.expected_keywords and not (check := contains_any(answer, turn.expected_keywords)):
            failed.append(f"turn {number}: {check.detail}")
        if turn.forbidden_words and not (check := contains_none(answer, turn.forbidden_words)):
            failed.append(f"turn {number}: {check.detail}")

    assert not failed, f"{case.description}\n{failed}\n{conversation.transcript()}"


def test_sessions_are_isolated(client):
    """A detail told in one session must not be known in another session."""
    first = Conversation(client)
    first.say("My name is Zorawar. Please remember it.")
    assert contains_any(first.say("What is my name?"), ["Zorawar"]), first.transcript()

    second = Conversation(client)
    answer = second.say("What is my name?")
    assert contains_none(answer, ["Zorawar"]), second.transcript()
