from __future__ import annotations

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from portal.config import settings
from portal.routers.listener import _build_embed_frame_policy


class SecurityHeadersMiddleware:
    """Add baseline security headers without overriding ones a route set itself.

    /embed/ keeps its configurable frame policy on every response, including errors,
    so third-party hosts still see the embed's error page instead of a blocked frame.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if scope["path"].startswith("/embed/"):
            frame_ancestors = _build_embed_frame_policy()[0]
        else:
            frame_ancestors = "frame-ancestors 'self'"

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
                headers.setdefault("Content-Security-Policy", frame_ancestors)
                if settings.is_https:
                    headers.setdefault("Strict-Transport-Security", "max-age=31536000")
            await send(message)

        await self.app(scope, receive, send_with_headers)
