from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.exceptions.user import UserNotFound
from app.middlewares.error_handling import ErrorHandlingMiddleware
from app.middlewares.request_validation import RequestValidationMiddleware
from app.middlewares.security_headers import SecurityHeadersMiddleware


@pytest.fixture
def base_app():
    """Base FastAPI app with routes that trigger different error scenarios"""
    app = FastAPI()

    @app.get("/success")
    async def success():
        return {"status": "ok"}

    @app.get("/domain-error")
    async def domain_error():
        raise UserNotFound("User with this ID was not found")

    @app.get("/value-error")
    async def value_error():
        raise ValueError("Invalid input data")

    @app.get("/unexpected-error")
    async def unexpected_error():
        raise RuntimeError("Database connection failed!")

    @app.post("/post")
    async def post():
        return {"status": "ok"}

    return app


@pytest.fixture
def app_factory(base_app):
    def _create_app(
        *,
        error_debug: bool | None = None,
        include_csp: bool | None = None,
        request_validation: dict | None = None,
    ):
        app = base_app

        if error_debug is not None:
            app.add_middleware(ErrorHandlingMiddleware, debug=error_debug)

        if include_csp is not None:
            app.add_middleware(SecurityHeadersMiddleware, include_csp=include_csp)

        if request_validation is not None:
            app.add_middleware(RequestValidationMiddleware, **request_validation)

        return app

    return _create_app


@pytest.fixture
def client(app_factory):
    return TestClient(app_factory(error_debug=False))


@pytest.fixture
def debug_client(app_factory):
    return TestClient(app_factory(error_debug=True))
