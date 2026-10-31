import pytest

pytestmark = pytest.mark.api


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"message": ""}, id="empty_message"),
        pytest.param({"message": "a" * 2001}, id="over_length_message"),
        pytest.param({}, id="missing_message_field"),
        pytest.param({"message": None}, id="null_message"),
        pytest.param({"message": 12345}, id="wrong_type_message"),
        pytest.param({"session_id": "abc"}, id="only_session_id"),
    ],
)
def test_invalid_payload_returns_422(client, payload):
    response = client.send_raw(payload)
    assert response.status_code == 422


def test_invalid_json_body_returns_422(client):
    response = client.request_raw(
        "POST", "/chat", content="not json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_wrong_http_method_returns_405(client, method):
    response = client.request_raw(method, "/chat")
    assert response.status_code == 405


def test_422_body_explains_the_error(client):
    response = client.send_raw({"message": ""})
    detail = response.json()["detail"]
    assert detail[0]["loc"] == ["body", "message"]
