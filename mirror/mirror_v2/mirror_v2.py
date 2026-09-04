#!/usr/bin/env python3

# ============================================================
# 91porny Mirror V2
# Stage 6.3 Skeleton
# ============================================================

from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)

from mirror_v2.core.proxy import ProxyCore


HOST = "127.0.0.1"
PORT = 8022


class MirrorV2Handler(BaseHTTPRequestHandler):

    protocol_version = "HTTP/1.1"

    proxy = ProxyCore()

    def log_message(self, format, *args):
        print(
            "[V2 HTTP]",
            format % args,
        )

    def do_GET(self):
        self.proxy.handle(self)

    def do_HEAD(self):
        self.proxy.handle(self)

    def do_POST(self):
        self.proxy.handle(self)

    def do_OPTIONS(self):
        self.proxy.handle(self)


def main():

    server = ThreadingHTTPServer(
        (HOST, PORT),
        MirrorV2Handler,
    )

    print("============================================================")
    print("91porny MIRROR V2")
    print("Stage : 6.3 Skeleton")
    print("Listen:", f"{HOST}:{PORT}")
    print("============================================================")

    server.serve_forever()


if __name__ == "__main__":
    main()
