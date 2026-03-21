import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.base import DomainException

logger = structlog.get_logger(__name__)


def build_error_response(
    *,
    status_code: int,
    error_type: str,
    message: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_type,
            "message": message,
        },
    )


def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainException):
        raise

    logger.warning(exc.message, status_code=exc.http_status, error=exc.error_type)

    return build_error_response(message=exc.get_message(), status_code=exc.http_status, error_type=exc.error_type)
