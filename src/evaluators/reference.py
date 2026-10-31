import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from src.evaluators.rules import normalize


@dataclass
class ScoreResult:
    score: float
    detail: str


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalize(text))


def fact_coverage(answer: str, facts: list[list[str]]) -> ScoreResult:
    """Share of facts found in the answer. Each fact is a list of variants; any one counts."""
    lowered = normalize(answer)
    missing = [f[0] for f in facts if not any(normalize(v) in lowered for v in f)]
    score = (len(facts) - len(missing)) / len(facts)
    detail = f"missing facts {missing}" if missing else "all facts found"
    return ScoreResult(score, detail)


def keyword_coverage(answer: str, keywords: list[str]) -> ScoreResult:
    """Share of the keywords that appear in the answer (case-insensitive)."""
    lowered = normalize(answer)
    missing = [k for k in keywords if normalize(k) not in lowered]
    score = (len(keywords) - len(missing)) / len(keywords)
    detail = f"missing keywords {missing}" if missing else "all keywords found"
    return ScoreResult(score, detail)


def similarity(answer: str, reference: str) -> ScoreResult:
    """Word-level difflib ratio (0 to 1) between the answer and a reference answer."""
    score = SequenceMatcher(None, _words(answer), _words(reference)).ratio()
    return ScoreResult(score, f"similarity {score:.2f}")
