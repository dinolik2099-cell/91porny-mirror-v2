# ============================================================
# 91porny Mirror V2
# HTML Rewrite Pipeline
# ============================================================

import re

from mirror_v2.rewrite.ad import rewrite_ad
from mirror_v2.rewrite.image import transform_image_url


def rewrite_html(data):

    text = data.decode(
        "utf-8",
        errors="replace",
    )

    # --------------------------------------------------------
    # Stage 6.7.9.4-R4:
    # Transform only confirmed video-image URLs.
    #
    # Unknown external images remain unchanged.
    # --------------------------------------------------------

    def replace_image_url(match):
        url = match.group(0)
        return transform_image_url(url)

    text = re.sub(
        r"(?:https?:)?//[^\s\"'<>]+",
        replace_image_url,
        text,
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
        text = text.replace(source, target)

    text = rewrite_ad(text)

    return text.encode("utf-8")
