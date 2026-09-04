# ============================================================
# 91porny Mirror V2
# Response Processor
# ============================================================

from mirror_v2.core.headers import (
    HOP_BY_HOP,
    SKIP_RESPONSE_HEADERS,
)
from mirror_v2.rewrite.location import rewrite_location


def send_response(handler, response, body):

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

    handler.send_response(
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
            value = rewrite_location(value)

        handler.send_header(
            key,
            value,
        )

    handler.send_header(
        "Content-Length",
        str(len(body)),
    )

    handler.end_headers()

    if handler.command != "HEAD":
        handler.wfile.write(body)
