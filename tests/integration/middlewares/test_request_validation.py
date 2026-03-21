from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def validation_client(app_factory):
    return TestClient(app_factory(request_validation={"required_headers": ["x-request-id"], "max_body_size": 10}))


def test_valid_request(validation_client):
    response = validation_client.post(
        "/post",
        headers={
            "x-request-id": "123",
            "content-type": "application/json",
        },
        json={"a": 1},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_required_header(validation_client):
    response = validation_client.post(
        "/post",
        headers={"content-type": "application/json"},
        json={"a": 1},
    )

    assert response.status_code == 400
    assert "Missing required header" in response.json()["error"]


def test_unsupported_content_type(validation_client):
    response = validation_client.post(
        "/post",
        headers={
            "x-request-id": "123",
            "content-type": "text/plain",
        },
        data="hello",
    )

    assert response.status_code == 415
    assert "Unsupported content type" in response.json()["error"]
