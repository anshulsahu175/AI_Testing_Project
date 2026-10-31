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
