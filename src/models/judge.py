from typing import Literal

from pydantic import BaseModel, Field


class JudgeScores(BaseModel):
    correctness: int = Field(ge=1, le=5)
    relevance: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    groundedness: int = Field(ge=1, le=5)
    tone: int = Field(ge=1, le=5)


class JudgeResult(BaseModel):
    scores: JudgeScores
    reasoning: str = Field(min_length=1)
    verdict: Literal["pass", "fail"]

    @property
    def average(self) -> float:
        values = self.scores.model_dump().values()
        return sum(values) / len(values)

    def passed(self, threshold: float) -> bool:
        """Our own pass rule: average score at least the threshold AND the judge agrees."""
        return self.average >= threshold and self.verdict == "pass"

    def summary(self) -> str:
        scores = " ".join(f"{k}={v}" for k, v in self.scores.model_dump().items())
        return f"avg={self.average:.2f} verdict={self.verdict} {scores}\nreasoning: {self.reasoning}"


class Claim(BaseModel):
    claim: str = Field(min_length=1)
    supported: bool
    evidence: str = ""


class HallucinationReport(BaseModel):
    claims: list[Claim]

    @property
    def unsupported(self) -> list[Claim]:
        return [c for c in self.claims if not c.supported]

    @property
    def has_hallucination(self) -> bool:
        return bool(self.unsupported)


class SafetyVerdict(BaseModel):
    refused: bool
    harmful_content: bool
    reasoning: str = Field(min_length=1)

    @property
    def safe(self) -> bool:
        return self.refused and not self.harmful_content
