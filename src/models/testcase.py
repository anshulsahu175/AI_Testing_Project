from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ApiCase(BaseModel):
    id: str
    question: str = Field(min_length=1)
    expected_keywords: list[str] = []
    match: Literal["any", "all"] = "any"
    forbidden_words: list[str] = []
    regex: str | None = None
    max_length: int = 2000


class ReferenceCase(BaseModel):
    id: str
    question: str = Field(min_length=1)
    expected_facts: list[list[str]] = Field(min_length=1)
    source: str
    reference_answer: str = Field(min_length=1)

    @field_validator("expected_facts", mode="before")
    @classmethod
    def wrap_single_facts(cls, facts: list) -> list:
        """Allow a plain string fact in YAML; store every fact as a list of variants."""
        return [[f] if isinstance(f, str) else f for f in facts]


class InjectionCase(BaseModel):
    id: str
    category: Literal["instruction_override", "system_prompt_leak", "role_play", "encoded", "context_poisoning"]
    prompt: str = Field(min_length=1)
    forbidden_words: list[str] = Field(min_length=1)
    expected_keywords: list[str] = []
    known_issue: str | None = None


class SafetyCase(BaseModel):
    id: str
    category: Literal["harmful", "pii", "off_topic"]
    prompt: str = Field(min_length=1)
    forbidden_words: list[str] = []


class Turn(BaseModel):
    say: str = Field(min_length=1)
    expected_keywords: list[str] = []
    forbidden_words: list[str] = []


class ConversationCase(BaseModel):
    id: str
    description: str
    turns: list[Turn] = Field(min_length=2)
