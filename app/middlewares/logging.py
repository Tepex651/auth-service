import time
import uuid

import structlog
from starlette.datastructures import MutableHeaders
from structlog.contextvars import bind_contextvars, clear_contextvars

logger = structlog.get_logger()


class RequestLoggingMiddleware:
    """
    Middleware for comprehensive request and response logging.

    Logs:
    - Request method, path, and query parameters
    - Client IP address
    - Response status code and processing time
    """

    def __init__(self, app, log_request_body: bool = False):
        """
        Initialize the logging middleware.

        Args:
            app: The ASGI application
            log_request_body: Whether to log request bodies (use with caution)
        """
        self.app = app
        self.log_request_body = log_request_body

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        clear_contextvars()

        headers = MutableHeaders(raw=scope["headers"])

        request_id = headers.get("X-Request-ID", str(uuid.uuid4()))

        method = scope["method"]
        path = scope["path"]
        client_id = scope["client"][0]

        bind_contextvars(request_id=request_id, method=method, path=path, client_ip=client_id)

        start_time = time.perf_counter()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = (time.perf_counter() - start_time) * 1000

                logger.info(
                    "Request completed",
                    status_code=message["status"],
                    duration_ms=round(duration, 2),
                )

            await send(message)

        await self.app(scope, receive, send_wrapper)
