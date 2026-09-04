# ============================================================
# 91porny Mirror V2
# Origin Fetcher
# ============================================================

from urllib.request import Request, urlopen
from urllib.error import HTTPError

from mirror_v2.core.headers import SKIP_REQUEST_HEADERS


class Fetcher:

    def __init__(self, source):
        self.source = source

    def build_source_url(self, path):
        return self.source + path

    def fetch(self, handler):

        headers = {}

        for key, value in handler.headers.items():

            if key.lower() in SKIP_REQUEST_HEADERS:
                continue

            headers[key] = value

        headers["Accept-Encoding"] = "identity"

        url = self.build_source_url(
            handler.path
        )

        request = Request(
            url,
            headers=headers,
            method=handler.command,
        )

        try:

            return urlopen(
                request,
                timeout=30,
            )

        except HTTPError as exc:

            return exc
