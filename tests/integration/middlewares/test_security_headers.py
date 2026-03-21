from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def security_client(app_factory):
    return TestClient(app_factory(include_csp=True))


def test_security_headers_are_present(security_client):
    response = security_client.get("/success")

    headers = response.headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "strict-origin-when-cross-origin"


def test_csp_is_added_by_default(security_client):
    response = security_client.get("/success")
    assert "content-security-policy" in response.headers


def test_csp_can_be_disabled(app_factory):
    client = TestClient(app_factory(include_csp=False))
    response = client.get("/success")
    assert "content-security-policy" not in response.headers
