import json
import re
from dataclasses import dataclass


@dataclass
class RuleResult:
    passed: bool
    detail: str

    def __bool__(self) -> bool:
        return self.passed


_UNICODE_SPACES = re.compile(r"[     ]")
_CURLY_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def normalize(text: str) -> str:
    """Lowercase and replace Unicode spaces/quotes that LLMs often emit (e.g. '5\\u202fGB')."""
    return _UNICODE_SPACES.sub(" ", text).translate(_CURLY_QUOTES).lower()


def contains_any(text: str, keywords: list[str]) -> RuleResult:
    """Pass if at least one keyword appears (case-insensitive)."""
    lowered = normalize(text)
    found = [k for k in keywords if normalize(k) in lowered]
    if found:
        return RuleResult(True, f"found {found}")
    return RuleResult(False, f"none of {keywords} found")


def contains_all(text: str, keywords: list[str]) -> RuleResult:
    """Pass if every keyword appears (case-insensitive)."""
    lowered = normalize(text)
    missing = [k for k in keywords if normalize(k) not in lowered]
    if missing:
        return RuleResult(False, f"missing {missing}")
    return RuleResult(True, "all keywords found")


def contains_none(text: str, forbidden: list[str]) -> RuleResult:
    """Pass if no forbidden word appears (case-insensitive)."""
    lowered = normalize(text)
    found = [w for w in forbidden if normalize(w) in lowered]
    if found:
        return RuleResult(False, f"forbidden words found {found}")
    return RuleResult(True, "no forbidden words")


def matches_regex(text: str, pattern: str) -> RuleResult:
    """Pass if the pattern matches anywhere in the text (case-insensitive)."""
    if re.search(pattern, text, flags=re.IGNORECASE):
        return RuleResult(True, f"pattern {pattern!r} matched")
    return RuleResult(False, f"pattern {pattern!r} not matched")


def length_between(text: str, min_len: int = 1, max_len: int = 2000) -> RuleResult:
    """Pass if the stripped text length is within [min_len, max_len]."""
    length = len(text.strip())
    if min_len <= length <= max_len:
        return RuleResult(True, f"length {length} ok")
    return RuleResult(False, f"length {length} not in [{min_len}, {max_len}]")


def is_valid_json(text: str) -> RuleResult:
    """Pass if the text parses as JSON."""
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        return RuleResult(False, f"invalid JSON: {exc}")
    return RuleResult(True, "valid JSON")
