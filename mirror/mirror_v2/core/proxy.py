# ============================================================
# 91porny Mirror V2
# Proxy Core
# ============================================================

from urllib.parse import urlsplit

from mirror_v2.core.fetcher import Fetcher
from mirror_v2.core.response import send_response
from mirror_v2.media.detector import is_media
from mirror_v2.media.image_route import resolve_image_proxy_path
from mirror_v2.rewrite.html import rewrite_html
from urllib.request import Request, urlopen


SOURCE = "https://91porny.com"


class ProxyCore:

    def __init__(self):
        self.fetcher = Fetcher(SOURCE)

    def handle(self, handler):

        parsed = urlsplit(handler.path)

        print(
            "[V2 REQUEST]",
            handler.command,
            parsed.path,
            parsed.query if parsed.query else "-",
        )

        # Stage 6.7.9.3.2:
        # Handle only internally mapped image proxy paths.
        if parsed.path.startswith("/image-proxy/"):

            if handler.command not in {"GET", "HEAD"}:
                handler.send_error(
                    405,
                    "Image proxy method not allowed",
                )
                return

            source_url, image_type = (
                resolve_image_proxy_path(
                    handler.path
                )
            )

            if not source_url:
                handler.send_error(
                    404,
                    "Image proxy resource not found",
                )
                return

            request = Request(
                source_url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                    "Accept-Encoding": "identity",
                },
                method=handler.command,
            )

            try:
                image_response = urlopen(
                    request,
                    timeout=15,
                )

            except Exception:
                handler.send_error(
                    502,
                    "Image proxy upstream error",
                )
                return

            body = image_response.read()

            send_response(
                handler,
                image_response,
                body,
            )

            return

        # Stage 6.3:
        # 保持 V1 的媒体边界。
        # 不主动代理真实媒体。
        if is_media(parsed.path):

            handler.send_error(
                404,
                "Media proxy disabled in V2 skeleton",
            )

            return

        response = self.fetcher.fetch(
            handler
        )

        body = response.read()

        content_type = response.headers.get(
            "Content-Type",
            "",
        )

        if "text/html" in content_type.lower():
            body = rewrite_html(body)

        send_response(
            handler,
            response,
            body,
        )
