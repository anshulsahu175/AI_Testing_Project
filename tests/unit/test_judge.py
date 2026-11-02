import json

import httpx
import pytest
from pydantic import ValidationError
from tenacity import wait_none

from src.clients.judge_client import GeminiClient, QuotaExhaustedError
from src.evaluators.judge import Judge, JudgeError
from src.models.judge import JudgeResult
from src.utils.cache import DiskCache

pytestmark = pytest.mark.unit

GOOD = {
    "scores": {"correctness": 5, "relevance": 5, "completeness": 4, "groundedness": 5, "tone": 4},
    "reasoning": "Matches the context.",
    "verdict": "pass",
}


class FakeClient:
    """Stands in for GeminiClient: returns the given replies in order and counts calls."""

    model = "fake-model"

    def __init__(self, *replies: str):
        self.replies = list(replies)
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.replies.pop(0)


@pytest.fixture
def cache(tmp_path) -> DiskCache:
    return DiskCache(tmp_path)


def test_evaluate_parses_valid_json(cache):
    result = Judge(FakeClient(json.dumps(GOOD)), cache).evaluate("q", "a", "ctx")
    assert result.average == pytest.approx(4.6)
    assert result.passed(threshold=4.0)
    assert not result.passed(threshold=4.8)


def test_fail_verdict_never_passes():
    result = JudgeResult.model_validate({**GOOD, "verdict": "fail"})
    assert not result.passed(threshold=1.0)


def test_scores_outside_1_to_5_are_rejected():
    bad = {**GOOD, "scores": {**GOOD["scores"], "tone": 6}}
    with pytest.raises(ValidationError):
        JudgeResult.model_validate(bad)


def test_markdown_fences_are_stripped(cache):
    client = FakeClient(f"```json\n{json.dumps(GOOD)}\n```")
    assert Judge(client, cache).evaluate("q", "a", "ctx").verdict == "pass"


def test_retries_on_invalid_json_then_succeeds(cache):
    client = FakeClient("not json", json.dumps(GOOD))
    Judge(client, cache).evaluate("q", "a", "ctx")
    assert len(client.prompts) == 2
    assert "could not be parsed" in client.prompts[1]


def test_gives_up_after_max_attempts(cache):
    client = FakeClient("{}", "{}", "{}")
    with pytest.raises(JudgeError):
        Judge(client, cache, max_attempts=3).evaluate("q", "a", "ctx")
    assert len(client.prompts) == 3


def test_cache_hit_skips_the_llm(cache):
    Judge(FakeClient(json.dumps(GOOD)), cache).evaluate("q", "a", "ctx")
    second = FakeClient()
    assert Judge(second, cache).evaluate("q", "a", "ctx").verdict == "pass"
    assert second.prompts == []


def test_invalid_output_is_not_cached(cache):
    with pytest.raises(JudgeError):
        Judge(FakeClient("bad"), cache, max_attempts=1).evaluate("q", "a", "ctx")
    assert Judge(FakeClient(json.dumps(GOOD)), cache).evaluate("q", "a", "ctx")


def test_hallucination_report_lists_unsupported_claims(cache):
    reply = {"claims": [
        {"claim": "Pro has 200 GB", "supported": True, "evidence": "200 GB of storage"},
        {"claim": "Pro includes a phone", "supported": False, "evidence": ""},
    ]}
    report = Judge(FakeClient(json.dumps(reply)), cache).check_hallucination("a", "ctx")
    assert report.has_hallucination
    assert [c.claim for c in report.unsupported] == ["Pro includes a phone"]


def _gemini_reply(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [
        {"text": "thinking...", "thought": True},
        {"text": text},
    ]}}]}


def test_gemini_client_request_and_retry():
    seen: list[httpx.Request] = []
    responses = [httpx.Response(503), httpx.Response(200, json=_gemini_reply('{"ok": true}'))]

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return responses.pop(0)

    client = GeminiClient(model="m", delay_seconds=0, wait=wait_none(),
                          transport=httpx.MockTransport(handler))
    assert client.generate("hi") == '{"ok": true}'
    assert len(seen) == 2
    assert "x-goog-api-key" in seen[0].headers
    body = json.loads(seen[0].content)
    assert body["generationConfig"] == {"temperature": 0, "responseMimeType": "application/json"}


def test_gemini_client_does_not_retry_client_errors():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(400)

    client = GeminiClient(model="m", delay_seconds=0, wait=wait_none(),
                          transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        client.generate("hi")
    assert len(calls) == 1


def test_gemini_client_fails_fast_when_daily_quota_is_used_up():
    calls = []
    error = {"error": {"message": "Quota exceeded", "details": [
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "17419s"},
    ]}}

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(429, json=error)

    client = GeminiClient(model="m", delay_seconds=0, wait=wait_none(),
                          transport=httpx.MockTransport(handler))
    with pytest.raises(QuotaExhaustedError, match="Quota exceeded"):
        client.generate("hi")
    assert len(calls) == 1
