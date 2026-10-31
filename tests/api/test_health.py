import pytest

pytestmark = pytest.mark.api


def test_health_returns_200(client):
    assert client.health()


def test_health_body_is_ok(client):
    response = client.request_raw("GET", "/health")
    assert response.json() == {"status": "ok"}


def test_unknown_endpoint_returns_404(client):
    response = client.request_raw("GET", "/does-not-exist")
    assert response.status_code == 404
