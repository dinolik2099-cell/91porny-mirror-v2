# ============================================================
# 91porny Mirror V2
# Header Policy
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
