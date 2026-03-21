from unittest.mock import patch


def test_success_request_passes_through(client):
    """Successful requests should not be affected by the middleware"""
    response = client.get("/success")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_domain_exception_is_handled(client):
    """DomainException should return proper status and error format"""
    response = client.get("/domain-error")

    assert response.status_code == 404
    data = response.json()

    assert data["error"]["type"] == "user_not_found"
    assert data["error"]["message"] == "User with this ID was not found"
    assert data["error"]["path"] == "/domain-error"


def test_value_error_is_converted_to_validation_error(client):
    """ValueError should be converted to 400 validation_error"""
    response = client.get("/value-error")

    assert response.status_code == 400
    data = response.json()

    assert data["error"]["type"] == "validation_error"
    assert "Invalid input data" in data["error"]["message"]


@patch("app.middlewares.error_handling.logger")
def test_unexpected_error_returns_500_and_is_logged(mock_logger, client):
    """Unexpected exceptions should return 500 and be logged"""
    response = client.get("/unexpected-error")

    assert response.status_code == 500
    data = response.json()

    assert data["error"]["type"] == "internal_error"
    assert data["error"]["message"] == "An unexpected error occurred"

    mock_logger.error.assert_called_once()


def test_debug_mode_includes_traceback(debug_client):
    """In debug mode, unexpected errors should include traceback"""
    response = debug_client.get("/unexpected-error")
    data = response.json()

    assert response.status_code == 500
    assert "debug" in data["error"]
    assert data["error"]["debug"]["exception_type"] == "RuntimeError"
