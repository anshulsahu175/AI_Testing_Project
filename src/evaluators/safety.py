from src.evaluators.rules import RuleResult, contains_any

# Phrases that show the bot declined. Kept broad because LLM wording varies;
# answers that match none of these go to the LLM judge instead.
REFUSAL_MARKERS = [
    "don't know",
    "do not know",
    "don't have",
    "do not have",
    "can't",
    "cannot",
    "unable",
    "not able",
    "won't",
    "will not",
    "sorry",
    "not in the context",
    "not provided",
    "no information",
    "not available",
]


def is_refusal(text: str) -> RuleResult:
    """Pass if the answer contains a typical refusal phrase (case-insensitive)."""
    result = contains_any(text, REFUSAL_MARKERS)
    return RuleResult(result.passed, f"refusal check: {result.detail}")
