import json

from fastapi import status
from starlette.datastructures import MutableHeaders


class RequestValidationMiddleware:
    """
    Middleware for request validation.

    Validates:
    - Content-Type headers
    - Request body size limits
    - Required headers
    - Path parameter patterns
    """

    def __init__(
        self,
        app,
        max_body_size: int = 1024 * 1024,  # 1 MB default
        required_headers: list[str] | None = None,
        allowed_content_types: list[str] | None = None,
    ):
        """
        Initialize validation middleware.

        Args:
            app: The ASGI application
            max_body_size: Maximum allowed request body size in bytes
            required_headers: List of headers that must be present
            allowed_content_types: List of allowed Content-Type values
        """
        self.app = app
        self.max_body_size = max_body_size
        self.required_headers = {header.lower() for header in (required_headers or [])}
        self.allowed_content_types = allowed_content_types or [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        method = scope["method"]

        if method not in ["POST", "PUT", "PATCH"]:
            return await self.app(scope, receive, send)

        # Check required headers
        headers = MutableHeaders(raw=scope["headers"])
        headers = {k.lower(): v for k, v in headers.items()}

        missing_headers = self.required_headers - headers.keys()
        if missing_headers:
            return await self._send_json(
                send, status.HTTP_400_BAD_REQUEST, {"error": f"Missing required header: {missing_headers}"}
            )
        # Check Content-Type for requests with body
        content_type = headers.get("content-type", "")
        content_type_base = content_type.split(";")[0].strip()

        if content_type_base and content_type_base not in self.allowed_content_types:
            return await self._send_json(
                send,
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                {"error": f"Unsupported content type: {content_type_base}"},
            )

        content_length = headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_size:
                    return await self._send_json(
                        send,
                        status.HTTP_413_CONTENT_TOO_LARGE,
                        {"error": "Request body too large"},
                    )
            except ValueError:
                return await self._send_json(
                    send,
                    status.HTTP_400_BAD_REQUEST,
                    {"error": "Invalid Content-Length header"},
                )

        received_size = 0

        async def receive_wrapper():
            nonlocal received_size

            message = await receive()

            if message["type"] == "http.request":
                body = message.get("body", b"")
                received_size += len(body)

                if received_size > self.max_body_size:
                    raise RequestTooLargeError()

            return message

        try:
            await self.app(scope, receive_wrapper, send)
        except RequestTooLargeError:
            await self._send_json(
                send,
                status.HTTP_413_CONTENT_TOO_LARGE,
                {"error": "Request body too large"},
            )

    async def _send_json(self, send, status: int, content: dict):
        body = json.dumps(content).encode()

        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )

        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )


class RequestTooLargeError(Exception):
    pass
