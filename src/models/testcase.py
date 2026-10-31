from typing import Literal

from pydantic import BaseModel, Field


class ApiCase(BaseModel):
    id: str
    question: str = Field(min_length=1)
    expected_keywords: list[str] = []
    match: Literal["any", "all"] = "any"
    forbidden_words: list[str] = []
    regex: str | None = None
    max_length: int = 2000
