from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from src.config.settings import settings
from src.evaluators.prompts import HALLUCINATION_PROMPT, JUDGE_PROMPT, RETRY_SUFFIX
from src.models.judge import HallucinationReport, JudgeResult
from src.utils.cache import DiskCache
from src.utils.logger import get_logger

log = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    model: str

    def generate(self, prompt: str) -> str: ...


class JudgeError(Exception):
    """The judge never returned output that matched the schema."""


def _strip_fences(text: str) -> str:
    """Remove ```json fences in case the model wraps its JSON in Markdown."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    return text.strip()


class Judge:
    def __init__(self, client: LLMClient, cache: DiskCache | None = None, max_attempts: int = 3):
        self.client = client
        self.cache = cache or DiskCache(settings.judge_cache_dir)
        self.max_attempts = max_attempts

    def _ask(self, prompt: str, schema: type[T]) -> T:
        """Return cached output, or call the LLM and retry until the reply fits the schema."""
        key = f"{self.client.model}\n{prompt}"
        cached = self.cache.get(key)
        if cached is not None:
            log.info("judge cache hit")
            return schema.model_validate_json(cached)

        current = prompt
        for attempt in range(1, self.max_attempts + 1):
            raw = self.client.generate(current)
            try:
                result = schema.model_validate_json(_strip_fences(raw))
            except ValidationError as error:
                log.warning("invalid judge output (attempt %d): %s", attempt, error)
                current = prompt + RETRY_SUFFIX.format(error=error.errors()[0]["msg"])
                continue
            self.cache.set(key, result.model_dump_json())
            return result
        raise JudgeError(f"no valid {schema.__name__} after {self.max_attempts} attempts")

    def evaluate(self, question: str, answer: str, context: str) -> JudgeResult:
        prompt = JUDGE_PROMPT.format(question=question, answer=answer, context=context)
        return self._ask(prompt, JudgeResult)

    def check_hallucination(self, answer: str, context: str) -> HallucinationReport:
        prompt = HALLUCINATION_PROMPT.format(answer=answer, context=context)
        return self._ask(prompt, HallucinationReport)
