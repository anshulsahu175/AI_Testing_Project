import re
from functools import lru_cache
from pathlib import Path

import yaml

ANSWERS_FILE = Path("data/mocks/bot_answers.yaml")
DONT_KNOW = "I'm sorry, I don't know. That information is not in my documents."
_NAME_TOLD = re.compile(r"\bmy name is (\w+)", re.IGNORECASE)


@lru_cache
def _answers() -> dict[str, str]:
    raw = yaml.safe_load(ANSWERS_FILE.read_text(encoding="utf-8"))
    return {item["question"].strip().lower(): item["answer"] for item in raw}


def mock_answer(question: str, history: list[dict]) -> str:
    """Offline stand-in for Groq: canned answers, plus remembering a name told in this session."""
    if "what is my name" in question.lower():
        for message in reversed(history):
            if message["role"] == "user" and (match := _NAME_TOLD.search(message["content"])):
                return f"Your name is {match.group(1)}."
        return DONT_KNOW
    return _answers().get(question.strip().lower(), DONT_KNOW)
