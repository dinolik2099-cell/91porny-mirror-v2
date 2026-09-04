"""
Stage 6.7.9.1
Video image URL transformer.

Scope:
    - Video thumbnail
    - Video screenshot
    - Video poster thumbnail

Design:
    - Only transform confirmed video-image hosts/paths.
    - Unknown external images remain unchanged.
    - No network access.
    - No image fetching.
"""

import re
from urllib.parse import urlsplit


# ------------------------------------------------------------
# Confirmed source hosts
# ------------------------------------------------------------

THUMBNAIL_HOSTS = {
    "int.ucloud161.xyz",
}

SCREENSHOT_HOSTS = {
    "i.ucloud161.xyz",
    "int.qiniuyun37.xyz",
}


# ------------------------------------------------------------
# URL classification
# ------------------------------------------------------------

def classify_image_url(url):
    """
    Return one of:

        VIDEO_THUMBNAIL
        VIDEO_SCREENSHOT
        UNKNOWN

    Classification is intentionally conservative.
    """

    if not isinstance(url, str):
        return "UNKNOWN"

    value = url.strip()

    if not value:
        return "UNKNOWN"

    # Protocol-relative URL:
    # //int.ucloud161.xyz/thumb/1234567.jpg
    #
    # Only normalize for classification. The actual transform
    # remains controlled by the confirmed host/path allowlists.
    parse_value = (
        "https:" + value
        if value.startswith("//")
        else value
    )

    try:
        parts = urlsplit(parse_value)
    except Exception:
        return "UNKNOWN"

    scheme = parts.scheme.lower()
    host = parts.netloc.lower()

    if scheme not in {"http", "https"}:
        return "UNKNOWN"

    if host in THUMBNAIL_HOSTS:
        if parts.path.startswith("/thumb/"):
            return "VIDEO_THUMBNAIL"

    if host in SCREENSHOT_HOSTS:
        if parts.path.startswith(
            "/contents/videos_screenshots/"
        ):
            return "VIDEO_SCREENSHOT"

        # i.ucloud161.xyz 视频卡片图片：
        # /YYYY/MM/DD/<十六进制文件名>.(jpg|jpeg|png|webp)
        #
        # 仅识别已经验证过的视频图片路径。
        # 其他 i.ucloud161.xyz 路径继续保持 UNKNOWN。
        if host == "i.ucloud161.xyz":
            if re.match(
                r"^/\d{4}/\d{2}/\d{2}/[a-f0-9]+\.(jpg|jpeg|png|webp)$",
                parts.path,
                re.IGNORECASE,
            ):
                return "VIDEO_SCREENSHOT"

    return "UNKNOWN"


# ------------------------------------------------------------
# URL transformation
# ------------------------------------------------------------

def transform_image_url(url):
    """
    Transform a confirmed video image URL.

    Unknown URLs are returned unchanged.
    """

    kind = classify_image_url(url)

    try:
        parts = urlsplit(url)
    except ValueError:
        return url

    host = parts.netloc.lower()

    if kind == "VIDEO_THUMBNAIL":
        parts = urlsplit(url)

        return (
            "/image-proxy"
            + parts.path
            + (
                "?" + parts.query
                if parts.query
                else ""
            )
        )

    if kind == "VIDEO_SCREENSHOT":
        parts = urlsplit(url)

        source_key = (
            "qiniu"
            if host == "int.qiniuyun37.xyz"
            else "i"
        )

        return (
            "/image-proxy/screenshots/"
            + source_key
            + parts.path
            + (
                "?" + parts.query
                if parts.query
                else ""
            )
        )

    return url


# ------------------------------------------------------------
# HTML attribute / CSS value helper
# ------------------------------------------------------------

def transform_image_value(value):
    """
    Transform a single image URL/value.

    This helper does not attempt to parse arbitrary HTML.
    HTML integration will be handled separately.
    """

    return transform_image_url(value)


__all__ = [
    "classify_image_url",
    "transform_image_url",
    "transform_image_value",
]
