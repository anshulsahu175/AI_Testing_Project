import time

import httpx
from tenacity import (
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)
from tenacity.wait import wait_base

from src.config.settings import settings
from src.utils.logger import get_logger

log = get_logger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
RETRY_STATUS = {429, 500, 502, 503, 504}
MAX_RETRY_DELAY_SECONDS = 60


class QuotaExhaustedError(Exception):
    """Gemini asked us to wait too long (e.g. the daily free-tier quota is used up)."""


def _retry_delay_seconds(response: httpx.Response) -> float:
    """Gemini's suggested wait from the RetryInfo detail of an error, 0 if missing."""
    try:
        details = response.json()["error"]["details"]
    except (ValueError, KeyError, TypeError):
        return 0.0
    for detail in details:
        if detail.get("@type", "").endswith("RetryInfo"):
            return float(detail.get("retryDelay", "0s").rstrip("s"))
    return 0.0


def _is_retryable(error: BaseException) -> bool:
    """Retry network errors, rate limits (429) and temporary server errors (5xx)."""
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code in RETRY_STATUS
    return isinstance(error, (httpx.TransportError, httpx.TimeoutException))


class GeminiClient:
    """Calls the Gemini REST API and returns the model's JSON text."""

    def __init__(
        self,
        model: str | None = None,
        delay_seconds: float | None = None,
        wait: wait_base | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        self.model = model or settings.gemini_model
        self.delay_seconds = settings.judge_delay_seconds if delay_seconds is None else delay_seconds
        self._last_call = 0.0
        self._client = httpx.Client(
            headers={"x-goog-api-key": settings.gemini_api_key},
            timeout=settings.judge_timeout,
            transport=transport,
        )
        self._retrying = Retrying(
            stop=stop_after_attempt(5),
            wait=wait or wait_exponential(min=4, max=60),
            retry=retry_if_exception(_is_retryable),
            reraise=True,
        )

    def _respect_rate_limit(self) -> None:
        """Keep at least delay_seconds between calls to stay inside the free-tier quota."""
        remaining = self._last_call + self.delay_seconds - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)
        self._last_call = time.monotonic()

    def _post(self, payload: dict) -> dict:
        self._respect_rate_limit()
        response = self._client.post(GEMINI_URL.format(model=self.model), json=payload)
        if response.status_code == 429 and _retry_delay_seconds(response) > MAX_RETRY_DELAY_SECONDS:
            raise QuotaExhaustedError(response.json()["error"]["message"])
        if response.status_code in RETRY_STATUS:
            log.warning("Gemini returned %s, retrying", response.status_code)
        response.raise_for_status()
        return response.json()

    def generate(self, prompt: str) -> str:
        """Send one prompt with temperature 0 and JSON output mode, return the reply text."""
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }
        log.info("Gemini %s prompt_chars=%d", self.model, len(prompt))
        data = self._retrying(self._post, payload)
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts if not p.get("thought"))

    def close(self) -> None:
        self._client.close()
