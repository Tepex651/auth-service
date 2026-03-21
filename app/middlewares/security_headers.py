from starlette.datastructures import MutableHeaders


class SecurityHeadersMiddleware:
    """
    Middleware that adds security headers to all responses.

    This helps protect against common web vulnerabilities like
    XSS, clickjacking, and MIME type sniffing attacks.
    """

    def __init__(self, app, include_csp: bool = True):
        """
        Initialize the middleware with configuration options.

        Args:
            app: The ASGI application
            include_csp: Whether to include Content-Security-Policy header
        """
        self.app = app
        self.include_csp = include_csp

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Modify headers before the request reaches the app
        async def send_with_security_headers(message: dict):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.update(
                    {
                        "X-Content-Type-Options": "nosniff",
                        "X-Frame-Options": "DENY",
                        "Referrer-Policy": "strict-origin-when-cross-origin",
                        "X-XSS-Protection": "1; mode=block",
                    }
                )

                if self.include_csp:
                    headers["Content-Security-Policy"] = (
                        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
                    )

            await send(message)

        await self.app(scope, receive, send_with_security_headers)
