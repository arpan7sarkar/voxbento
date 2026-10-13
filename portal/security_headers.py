from __future__ import annotations

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from portal.config import settings


class SecurityHeadersMiddleware:
    """Add baseline security headers without overriding ones a route set itself, such as the /embed/ frame policy."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
                headers.setdefault("Content-Security-Policy", "frame-ancestors 'self'")
                if settings.is_https:
                    headers.setdefault("Strict-Transport-Security", "max-age=31536000")
            await send(message)

        await self.app(scope, receive, send_with_headers)
