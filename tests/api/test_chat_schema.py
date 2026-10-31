import time

import pytest

from src.config.settings import settings
from src.evaluators.rules import length_between
from src.models.chat import ChatResponse

pytestmark = pytest.mark.api


def test_response_matches_schema(client):
    response = client.send_raw({"message": "What plans do you offer?"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    ChatResponse.model_validate(response.json())


def test_answer_is_not_empty(pricing_response):
    result = length_between(pricing_response.answer, min_len=1, max_len=2000)
    assert result, result.detail


def test_session_id_is_echoed(pricing_response):
    assert pricing_response.session_id == "schema-test"


def test_sources_point_to_pricing_doc(pricing_response):
    assert "pricing.txt" in pricing_response.sources


def test_server_latency_under_threshold(pricing_response):
    assert pricing_response.latency_ms is not None
    assert pricing_response.latency_ms < settings.max_latency_ms


def test_client_latency_under_threshold(client):
    start = time.perf_counter()
    client.send("Is there a refund policy?")
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < settings.max_latency_ms
