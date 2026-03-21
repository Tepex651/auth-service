import uvicorn
from fastapi import APIRouter, FastAPI

from app.api.exceptions import domain_exception_handler
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.me import router as me_router
from app.api.v1.routers.user import router as user_router
from app.bootstrap import bootstrap_app
from app.containers.enums import LogLevel
from app.db.session import init_db
from app.exceptions.base import DomainException
from app.middlewares.error_handling import ErrorHandlingMiddleware
from app.middlewares.logging import RequestLoggingMiddleware
from app.middlewares.request_validation import RequestValidationMiddleware
from app.middlewares.security_headers import SecurityHeadersMiddleware
from app.settings import Settings, get_settings


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI()

    _setup_core(app, settings)
    _setup_routers(app)
    _setup_exception_handlers(app)
    _setup_middlewares(app, settings)

    return app


def _setup_core(app: FastAPI, settings: Settings) -> None:
    bootstrap_app(settings)
    init_db(settings.db)
    app.state.settings = settings


def _setup_routers(app: FastAPI) -> None:
    api_router = APIRouter(prefix="/api")

    api_router.include_router(auth_router)
    api_router.include_router(me_router)
    api_router.include_router(user_router)

    app.include_router(api_router)


def _setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainException, domain_exception_handler)


def _setup_middlewares(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(SecurityHeadersMiddleware, include_csp=True)
    app.add_middleware(ErrorHandlingMiddleware, debug=settings.app.log_level == LogLevel.DEBUG)
    app.add_middleware(RequestLoggingMiddleware, log_request_body=settings.app.log_level == LogLevel.DEBUG)
    app.add_middleware(RequestValidationMiddleware, max_body_size=1024 * 1024)


settings = get_settings()
app = create_app(settings)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app.app_host,
        port=int(settings.app.app_port),
        reload=False,
    )
