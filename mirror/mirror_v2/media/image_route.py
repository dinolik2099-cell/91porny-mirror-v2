from urllib.parse import urlsplit, parse_qsl, urlencode


THUMBNAIL_SOURCE = "https://int.ucloud161.xyz"

SCREENSHOT_SOURCES = {
    "i": "https://i.ucloud161.xyz",
    "qiniu": "https://int.qiniuyun37.xyz",
}


def resolve_image_proxy_path(path):
    """
    Resolve an internal image-proxy path.

    Returns:
        source_url, image_type

    or:
        None, None

    No network access.
    """

    if not isinstance(path, str):
        return None, None

    parts = urlsplit(path)

    if parts.scheme or parts.netloc:
        return None, None

    pathname = parts.path

    # --------------------------------------------------------
    # Thumbnail
    # --------------------------------------------------------

    prefix = "/image-proxy/thumb/"

    if pathname.startswith(prefix):
        relative = pathname[len(prefix):]

        if not relative:
            return None, None

        if ".." in relative:
            return None, None

        if relative.startswith("/"):
            return None, None

        source = (
            THUMBNAIL_SOURCE
            + "/thumb/"
            + relative
        )

        if parts.query:
            source += "?" + parts.query

        return source, "VIDEO_THUMBNAIL"

    # --------------------------------------------------------
    # Screenshot
    # --------------------------------------------------------

    prefix = "/image-proxy/screenshots/"

    if pathname.startswith(prefix):
        relative = pathname[len(prefix):]

        pieces = relative.split("/", 1)

        if len(pieces) != 2:
            return None, None

        source_key, source_path = pieces

        if source_key not in SCREENSHOT_SOURCES:
            return None, None

        if not source_path:
            return None, None

        if ".." in source_path:
            return None, None

        if source_path.startswith("/"):
            return None, None

        source = (
            SCREENSHOT_SOURCES[source_key]
            + "/"
            + source_path
        )

        if parts.query:
            source += "?" + parts.query

        return source, "VIDEO_SCREENSHOT"

    return None, None


__all__ = [
    "resolve_image_proxy_path",
]
