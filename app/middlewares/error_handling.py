import logging
import traceback
from collections.abc import MutableMapping
from typing import Any

from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.exceptions.base import DomainException

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    def __init__(self, app: ASGIApp, debug: bool = False):
        self.app = app
        self.debug = debug

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def wrapped_send(message: MutableMapping[str, Any]):
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)

        except DomainException as e:
            logger.warning(f"{type(e).__name__}: {e.get_message()} | path={scope.get('path', '')}")
            response = self._create_error_response(
                status_code=e.http_status,
                error_type=e.error_type,
                message=e.get_message(),
                scope=scope,
                exception=e,
            )
            await response(scope, receive, send)

        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            response = self._create_error_response(
                status_code=400,
                error_type="validation_error",
                message=str(e),
                scope=scope,
            )
            await response(scope, receive, send)

        except Exception as e:  # noqa: BLE001
            logger.error(f"Unhandled exception: {e}\n{traceback.format_exc()}")
            response = self._create_error_response(
                status_code=500,
                error_type="internal_error",
                message="An unexpected error occurred",
                scope=scope,
                exception=e,
            )
            await response(scope, receive, send)

    def _create_error_response(
        self,
        status_code: int,
        error_type: str,
        message: str,
        scope: Scope,
        exception: Exception | None = None,
    ) -> JSONResponse:
        error_body: dict[str, Any] = {
            "error": {
                "type": error_type,
                "message": message,
                "path": scope.get("path", ""),
            }
        }

        if self.debug and exception:
            error_body["error"]["debug"] = {
                "exception_type": type(exception).__name__,
                "traceback": traceback.format_exc(),
            }

        return JSONResponse(status_code=status_code, content=error_body)
