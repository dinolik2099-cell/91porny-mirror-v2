#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import os


# ============================================================
# 91porny.com MIRROR
# Stage 3 / Basic Page Mirror / V1
# ============================================================

SOURCE = "https://91porny.com"

HOST = "127.0.0.1"
PORT = 8021


# ============================================================
# MEDIA
#
# Stage 3 暂不处理真实媒体。
# 后续进入阶段 4 / 5 后单独研究。
# ============================================================

MEDIA_EXTENSIONS = (
    ".m3u8",
    ".mp4",
    ".m4v",
    ".webm",
    ".mov",
    ".ts",
    ".m4s",
    ".mpd",
)


# ============================================================
# HTTP HEADER POLICY
# ============================================================

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


SKIP_REQUEST_HEADERS = {
    "host",
    "content-length",
    "connection",
}


SKIP_RESPONSE_HEADERS = {
    "content-length",
    "content-encoding",
    "connection",
}


# ============================================================
# HANDLER
# ============================================================

class MirrorHandler(BaseHTTPRequestHandler):

    protocol_version = "HTTP/1.1"

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    def log_message(self, fmt, *args):
        print("[MIRROR]", fmt % args)

    # --------------------------------------------------------
    # MEDIA CHECK
    # --------------------------------------------------------

    def is_media(self, path):

        path_lower = path.lower().split("?", 1)[0]

        return path_lower.endswith(MEDIA_EXTENSIONS)

    # --------------------------------------------------------
    # SOURCE URL
    # --------------------------------------------------------

    def build_source_url(self):

        return SOURCE + self.path

    # --------------------------------------------------------
    # FETCH SOURCE
    # --------------------------------------------------------

    def fetch(self):

        target = self.build_source_url()

        headers = {}

        for key, value in self.headers.items():

            if key.lower() in SKIP_REQUEST_HEADERS:
                continue

            headers[key] = value

        # 要求源站返回未压缩内容，
        # 方便后续 HTML / JS 处理。
        headers["Accept-Encoding"] = "identity"

        body = None

        # ----------------------------------------------------
        # POST / PUT / PATCH
        # ----------------------------------------------------

        if self.command in (
            "POST",
            "PUT",
            "PATCH",
        ):

            content_length = self.headers.get(
                "Content-Length"
            )

            if content_length:

                try:
                    length = int(content_length)

                except ValueError:
                    length = 0

                if length > 0:
                    body = self.rfile.read(length)

        request = Request(
            target,
            data=body,
            headers=headers,
            method=self.command,
        )

        try:

            return urlopen(
                request,
                timeout=30,
            )

        except HTTPError as exc:

            return exc

    # --------------------------------------------------------
    # LOCATION REWRITE
    # --------------------------------------------------------

    def rewrite_location(self, value):

        if not value:
            return value

        source_variants = (
            SOURCE,
            "https://www.91porny.com",
            "http://91porny.com",
            "http://www.91porny.com",
        )

        for source in source_variants:

            if value.startswith(source):

                value = value[len(source):]

                if not value:
                    value = "/"

                break

        return value

    # --------------------------------------------------------
    # HTML URL REWRITE
    #
    # 目前只处理 91porny.com 自身域名。
    #
    # 第三方资源暂时保持原样。
    # --------------------------------------------------------

    def rewrite_html(self, data):

        text = data.decode(
            "utf-8",
            errors="replace",
        )

        replacements = (
            (
                "https://www.91porny.com",
                "",
            ),
            (
                "http://www.91porny.com",
                "",
            ),
            (
                "https://91porny.com",
                "",
            ),
            (
                "http://91porny.com",
                "",
            ),
            (
                "//www.91porny.com",
                "",
            ),
            (
                "//91porny.com",
                "",
            ),
        )

        for source, target in replacements:

            text = text.replace(
                source,
                target,
            )

        return text.encode("utf-8")

    # --------------------------------------------------------
    # MAIN PROXY
    # --------------------------------------------------------

    def handle_proxy(self):

        parsed = urlsplit(self.path)

        print(
            "[V1 REQUEST]",
            self.command,
            parsed.path,
            parsed.query if parsed.query else "-",
        )

        # ----------------------------------------------------
        # Stage 3:
        # 暂时明确排除真实媒体。
        # ----------------------------------------------------

        if self.is_media(parsed.path):

            self.send_error(
                404,
                "Media proxy disabled in Stage 3",
            )

            return

        # ----------------------------------------------------
        # FETCH
        # ----------------------------------------------------

        try:

            response = self.fetch()

        except Exception as exc:

            print(
                "[V1 FETCH ERROR]",
                repr(exc),
            )

            self.send_error(
                502,
                "Upstream fetch failed",
            )

            return

        status = getattr(
            response,
            "status",
            200,
        )

        reason = getattr(
            response,
            "reason",
            "",
        )

        body = response.read()

        content_type = response.headers.get(
            "Content-Type",
            "",
        )

        # ----------------------------------------------------
        # HTML
        # ----------------------------------------------------

        if "text/html" in content_type.lower():

            body = self.rewrite_html(body)

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        self.send_response(
            status,
            reason,
        )

        for key, value in response.headers.items():

            lower = key.lower()

            if lower in HOP_BY_HOP:
                continue

            if lower in SKIP_RESPONSE_HEADERS:
                continue

            if lower == "location":

                value = self.rewrite_location(
                    value
                )

            self.send_header(
                key,
                value,
            )

        self.send_header(
            "Content-Length",
            str(len(body)),
        )

        self.end_headers()

        if self.command != "HEAD":

            self.wfile.write(body)

    # --------------------------------------------------------
    # METHODS
    # --------------------------------------------------------

    def do_GET(self):
        self.handle_proxy()

    def do_HEAD(self):
        self.handle_proxy()

    def do_POST(self):
        self.handle_proxy()

    def do_OPTIONS(self):
        self.handle_proxy()


# ============================================================
# MAIN
# ============================================================

def main():

    server = ThreadingHTTPServer(
        (HOST, PORT),
        MirrorHandler,
    )

    print("=" * 60)
    print("91porny.com Mirror V1")
    print("=" * 60)
    print("Listen :", f"{HOST}:{PORT}")
    print("Source :", SOURCE)
    print("Stage  : 3 / Basic Page Mirror")
    print("Media  : DISABLED")
    print("=" * 60)

    server.serve_forever()


if __name__ == "__main__":
    main()
