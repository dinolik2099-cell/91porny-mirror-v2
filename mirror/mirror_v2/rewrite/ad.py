# ============================================================
# 91porny Mirror V2
# Stable Advertisement Transformer
# Stage 6.6R6.1
#
# IMPORTANT:
# - Does NOT depend on source-site randomized CSS classes.
# - Does NOT modify video data-src.
# - Does NOT modify HLS URLs.
# - Does NOT proxy media.
# ============================================================

import re

from mirror_v2.config import ad_config


# ============================================================
# STABLE PRE-ROLL SIGNATURE
# ============================================================

COUNTDOWN_MARKER = "倒计时"
SKIP_MARKER = "跳过"


# ============================================================
# VIDEO CARD ADVERTISEMENT RULES
# ============================================================

# Each rule is deliberately tied to one advertising type.  A matching href
# alone is insufficient to remove arbitrary markup elsewhere on a page.
VIDEO_CARD_AD_BLACKLIST = {
    "https://evexymcv.cxksgtl.cc:6704/88.html?cid=4957645",
}


# Image-banner cells use a different DOM structure from video cards.  Keep
# their rules separate even when an advertising destination happens to match.
BANNER_IMAGE_AD_BLACKLIST = {
    "https://evexymcv.cxksgtl.cc:6704/88.html?cid=4957645",
    "https://psuu.bahwhr.cc/",
}


# Text slots are alert-style blocks and are intentionally kept separate from
# image-banner cells, even where both share a destination URL.
TEXT_SLOT_AD_BLACKLIST = {
    "https://evexymcv.cxksgtl.cc:6704/88.html?cid=4957645",
}


# This video-card layout is rendered in a .colVideoList wrapper instead of
# the homepage .col-30/.video-elem.mb-3 grid used by VIDEO_CARD_AD_BLACKLIST.
VIDEO_LIST_CARD_AD_BLACKLIST = {
    "https://psuu.bahwhr.cc/",
}


# ============================================================
# HELPERS
# ============================================================

def _find_pre_roll(text):
    """
    Locate the complete pre-roll advertisement container.

    Boundary strategy:

    1. Locate the stable countdown marker.
    2. Search backwards for a nearby <div ... data-nosnippet>.
    3. From that opening <div>, scan forward while tracking
       nested <div> / </div> depth.
    4. Return the complete outer advertisement container.

    This avoids relying on the first </div> after the countdown,
    which is unsafe because the advertisement contains nested divs.
    """

    countdown_pos = text.find("倒计时")

    if countdown_pos < 0:
        return None

    search_start = max(0, countdown_pos - 5000)

    opening_pattern = re.compile(
        r"<div\b[^>]*\bdata-nosnippet\b[^>]*>",
        re.IGNORECASE,
    )

    candidates = list(
        opening_pattern.finditer(
            text,
            search_start,
            countdown_pos + 1,
        )
    )

    if not candidates:
        return None

    root = candidates[-1]

    root_start = root.start()
    root_end = root.end()

    tag_pattern = re.compile(
        r"<(/?)div\b[^>]*>",
        re.IGNORECASE,
    )

    depth = 0

    for match in tag_pattern.finditer(
        text,
        root_start,
    ):
        token = match.group(0)

        if token.startswith("</"):
            depth -= 1

            if depth == 0:
                return (
                    root_start,
                    match.end(),
                )

        else:
            depth += 1

    return None

def _extract_ad_urls(block):
    """
    Extract advertisement URLs from the detected pre-roll block.

    This helper is intentionally side-effect free.

    The current transformer only needs stable detection of the
    original pre-roll boundary. The extracted URLs are retained
    as compatibility information and are not used to determine
    the configured V2 advertisement destination or media URL.
    """

    if not block:
        return {
            "redirect_url": None,
            "media_url": None,
        }

    redirect_url = None
    media_url = None

    anchor_match = re.search(
        r'<a\b[^>]*\bhref=["\']([^"\']+)["\']',
        block,
        re.IGNORECASE,
    )

    if anchor_match:
        redirect_url = anchor_match.group(1)

    image_match = re.search(
        r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']',
        block,
        re.IGNORECASE,
    )

    if image_match:
        media_url = image_match.group(1)

    return {
        "redirect_url": redirect_url,
        "media_url": media_url,
    }


def _has_video_card_classes(opening_tag):
    """Return whether an opening div is a video-card container."""

    class_match = re.search(
        r'\bclass\s*=\s*["\']([^"\']*)["\']',
        opening_tag,
        re.IGNORECASE,
    )

    if not class_match:
        return False

    classes = set(class_match.group(1).split())

    return {"video-elem", "mb-3"}.issubset(classes)


def _has_video_card_slot_classes(opening_tag):
    """Return whether an opening div is the outer grid slot of a video card."""

    class_match = re.search(
        r'\bclass\s*=\s*["\']([^"\']*)["\']',
        opening_tag,
        re.IGNORECASE,
    )

    if not class_match:
        return False

    classes = set(class_match.group(1).split())

    return {"col-30", "col-sm-20", "col-md-15"}.issubset(classes)


def _has_banner_image_cell_classes(opening_tag):
    """Return whether an opening div is a single banner-grid cell."""

    class_match = re.search(
        r'\bclass\s*=\s*["\']([^"\']*)["\']',
        opening_tag,
        re.IGNORECASE,
    )

    if not class_match:
        return False

    return "col-sm" in set(class_match.group(1).split())


def _has_video_list_card_classes(opening_tag):
    """Return whether an opening div is the outer slot of a list video card."""

    class_match = re.search(
        r'\bclass\s*=\s*["\']([^"\']*)["\']',
        opening_tag,
        re.IGNORECASE,
    )

    if not class_match:
        return False

    return "colVideoList" in set(class_match.group(1).split())


def _has_video_elem_class(opening_tag):
    """Return whether an opening div is an inner video element."""

    class_match = re.search(
        r'\bclass\s*=\s*["\']([^"\']*)["\']',
        opening_tag,
        re.IGNORECASE,
    )

    if not class_match:
        return False

    return "video-elem" in set(class_match.group(1).split())


def _find_matching_div_end(text, opening_start):
    """Return the end offset of a div container, respecting nested divs."""

    tag_pattern = re.compile(r"<(/?)div\b[^>]*>", re.IGNORECASE)
    depth = 0

    for match in tag_pattern.finditer(text, opening_start):
        if match.group(1):
            depth -= 1
            if depth == 0:
                return match.end()
        else:
            depth += 1

    return None


def _remove_video_card_ads(text):
    """Remove blacklisted advertisements only from full video-card containers."""

    container_pattern = re.compile(r"<div\b[^>]*>", re.IGNORECASE)
    href_pattern = re.compile(
        r'<a\b[^>]*\bhref\s*=\s*["\']([^"\']+)["\'][^>]*>',
        re.IGNORECASE,
    )
    blacklist_hits = 0
    containers_removed = 0
    cursor = 0
    output = []

    for container_match in container_pattern.finditer(text):
        if container_match.start() < cursor:
            continue

        opening_tag = container_match.group(0)

        is_video_card = _has_video_card_classes(opening_tag)
        is_video_card_slot = _has_video_card_slot_classes(opening_tag)

        if not is_video_card and not is_video_card_slot:
            continue

        container_end = _find_matching_div_end(text, container_match.start())

        if container_end is None:
            continue

        container_html = text[container_match.start():container_end]

        if is_video_card_slot:
            has_video_card_child = any(
                _has_video_card_classes(match.group(0))
                for match in container_pattern.finditer(
                    container_html,
                )
            )

            if not has_video_card_child:
                continue

        hrefs = {
            match.group(1).strip()
            for match in href_pattern.finditer(container_html)
        }

        matched_hrefs = hrefs.intersection(VIDEO_CARD_AD_BLACKLIST)

        if not matched_hrefs:
            continue

        output.append(text[cursor:container_match.start()])
        cursor = container_end
        blacklist_hits += len(matched_hrefs)
        containers_removed += 1

    if not containers_removed:
        print("[VIDEO_CARD_AD] blacklist_hits=0 containers_removed=0")
        return text

    output.append(text[cursor:])
    print(
        "[VIDEO_CARD_AD] "
        f"blacklist_hits={blacklist_hits} "
        f"containers_removed={containers_removed}"
    )
    return "".join(output)


def _remove_video_list_card_ads(text):
    """Remove blacklisted cards only from complete .colVideoList wrappers."""

    container_pattern = re.compile(r"<div\b[^>]*>", re.IGNORECASE)
    href_pattern = re.compile(
        r'<a\b[^>]*\bhref\s*=\s*["\']([^"\']+)["\'][^>]*>',
        re.IGNORECASE,
    )
    blacklist_hits = 0
    containers_removed = 0
    cursor = 0
    output = []

    for container_match in container_pattern.finditer(text):
        if container_match.start() < cursor:
            continue

        opening_tag = container_match.group(0)

        if not _has_video_list_card_classes(opening_tag):
            continue

        container_end = _find_matching_div_end(text, container_match.start())

        if container_end is None:
            continue

        container_html = text[container_match.start():container_end]
        has_video_element = any(
            _has_video_elem_class(match.group(0))
            for match in container_pattern.finditer(container_html)
        )

        if not has_video_element:
            continue

        matched_hrefs = {
            match.group(1).strip()
            for match in href_pattern.finditer(container_html)
        }.intersection(VIDEO_LIST_CARD_AD_BLACKLIST)

        if not matched_hrefs:
            continue

        output.append(text[cursor:container_match.start()])
        cursor = container_end
        blacklist_hits += len(matched_hrefs)
        containers_removed += 1

    if not containers_removed:
        print("[VIDEO_LIST_CARD_AD] blacklist_hits=0 containers_removed=0")
        return text

    output.append(text[cursor:])
    print(
        "[VIDEO_LIST_CARD_AD] "
        f"blacklist_hits={blacklist_hits} "
        f"containers_removed={containers_removed}"
    )
    return "".join(output)


def _remove_banner_image_ads(text):
    """Remove only blacklisted image-banner cells from their grid rows."""

    container_pattern = re.compile(r"<div\b[^>]*>", re.IGNORECASE)
    href_pattern = re.compile(
        r'<a\b[^>]*\bhref\s*=\s*["\']([^"\']+)["\'][^>]*>',
        re.IGNORECASE,
    )
    image_pattern = re.compile(
        r'<img\b[^>]*\bclass\s*=\s*["\'][^"\']*\bimg\b[^"\']*["\'][^>]*>',
        re.IGNORECASE,
    )
    blacklist_hits = 0
    cells_removed = 0
    cursor = 0
    output = []

    for container_match in container_pattern.finditer(text):
        if container_match.start() < cursor:
            continue

        opening_tag = container_match.group(0)

        if not _has_banner_image_cell_classes(opening_tag):
            continue

        container_end = _find_matching_div_end(text, container_match.start())

        if container_end is None:
            continue

        container_html = text[container_match.start():container_end]
        matched_hrefs = {
            match.group(1).strip()
            for match in href_pattern.finditer(container_html)
        }.intersection(BANNER_IMAGE_AD_BLACKLIST)

        if not matched_hrefs or not image_pattern.search(container_html):
            continue

        output.append(text[cursor:container_match.start()])
        cursor = container_end
        blacklist_hits += len(matched_hrefs)
        cells_removed += 1

    if not cells_removed:
        print("[BANNER_IMAGE_AD] blacklist_hits=0 cells_removed=0")
        return text

    output.append(text[cursor:])
    print(
        "[BANNER_IMAGE_AD] "
        f"blacklist_hits={blacklist_hits} cells_removed={cells_removed}"
    )
    return "".join(output)


def _remove_text_slot_ads(text):
    """Remove only blacklisted alert-style text-ad cells from their grid rows."""

    container_pattern = re.compile(r"<div\b[^>]*>", re.IGNORECASE)
    href_pattern = re.compile(
        r'<a\b[^>]*\bhref\s*=\s*["\']([^"\']+)["\'][^>]*>',
        re.IGNORECASE,
    )
    alert_pattern = re.compile(
        r'<div\b[^>]*\bclass\s*=\s*["\'][^"\']*\balert\b[^"\']*["\'][^>]*>',
        re.IGNORECASE,
    )
    text_pattern = re.compile(
        r'<span\b[^>]*\bclass\s*=\s*["\'][^"\']*\btext-danger\b[^"\']*["\'][^>]*>',
        re.IGNORECASE,
    )
    blacklist_hits = 0
    cells_removed = 0
    cursor = 0
    output = []

    for container_match in container_pattern.finditer(text):
        if container_match.start() < cursor:
            continue

        opening_tag = container_match.group(0)

        if not _has_banner_image_cell_classes(opening_tag):
            continue

        container_end = _find_matching_div_end(text, container_match.start())

        if container_end is None:
            continue

        container_html = text[container_match.start():container_end]
        matched_hrefs = {
            match.group(1).strip()
            for match in href_pattern.finditer(container_html)
        }.intersection(TEXT_SLOT_AD_BLACKLIST)

        if (
            not matched_hrefs
            or not alert_pattern.search(container_html)
            or not text_pattern.search(container_html)
        ):
            continue

        output.append(text[cursor:container_match.start()])
        cursor = container_end
        blacklist_hits += len(matched_hrefs)
        cells_removed += 1

    if not cells_removed:
        print("[TEXT_SLOT_AD] blacklist_hits=0 cells_removed=0")
        return text

    output.append(text[cursor:])
    print(
        "[TEXT_SLOT_AD] "
        f"blacklist_hits={blacklist_hits} cells_removed={cells_removed}"
    )
    return "".join(output)


def _build_ad_html():
    """
    Build a self-contained configurable pre-roll.

    Randomized CSS class names are generated locally so the
    transformer itself does not depend on source-site class
    names.
    """

    redirect_url = str(
        ad_config.AD_REDIRECT_URL
    ).strip()

    media_url = str(
        ad_config.AD_MEDIA_URL
    ).strip()

    countdown = max(
        0,
        int(ad_config.AD_COUNTDOWN),
    )

    allow_skip = bool(
        ad_config.AD_ALLOW_SKIP
    )

    cookie_name = str(
        ad_config.AD_COOKIE_NAME
    ).strip()

    cookie_max_age = max(
        0,
        int(ad_config.AD_COOKIE_MAX_AGE),
    )

    if not redirect_url:
        redirect_url = "#"

    if not media_url:
        media_url = ""

    cover_class = "mv2ad-cover"
    image_class = "mv2ad-image"
    control_class = "mv2ad-control"
    timer_class = "mv2ad-timer"
    skip_class = "mv2ad-skip"

    skip_html = ""

    if allow_skip:
        skip_html = f"""
        <div class="{skip_class} cursor-p">
            <span>跳过</span>
            <i class="fas fa-caret-right"></i>
        </div>
"""

    return f"""
<div class="{cover_class}" data-nosnippet>
    <style>
        .{cover_class} {{
            position:absolute;
            top:0;
            left:0;
            width:100%;
            height:100%;
            background-color:green;
            z-index:9999;
        }}

        .{image_class},
        .{image_class} img {{
            width:100%;
            height:100%;
        }}

        .{image_class} img {{
            display:block;
            object-fit:contain;
        }}

        .{control_class} {{
            position:absolute;
            bottom:50px;
            right:0;
            color:#fff;
            display:flex;
            flex-direction:column;
            align-items:flex-end;
        }}

        .{timer_class} {{
            font-size:12px;
            margin-bottom:5px;
            padding:2px;
            color:rgba(255,255,255,.9);
        }}

        .{skip_class} {{
            padding:5px 0 5px 10px;
            font-weight:lighter;
            background:rgba(0,0,0,.4);
            color:#fff;
            text-decoration:none;
            border:1px solid #d9d9d9;
            border-right:none!important;
        }}

        .{skip_class} span {{
            display:inline-block;
            margin-right:5px;
            min-width:50px;
            text-align:center;
        }}

        .{skip_class}:hover {{
            border-color:#fff;
        }}
    </style>

    <div class="{image_class}">
        <a href="{redirect_url}" target="_blank" rel="noopener nofollow">
            <img src="{media_url}" decoding="async">
        </a>
    </div>

    <div class="{control_class}">
        <div class="{timer_class}">
            倒计时<span class="text-danger"></span>秒
        </div>

        {skip_html}
    </div>
</div>

<script>
(function () {{

    var layer = document.querySelector(
        ".{cover_class}"
    );

    if (!layer) return;

    var remain = {countdown};
    var timer = null;

    var close = function () {{

        if (timer) {{
            window.clearTimeout(timer);
        }}

        layer.style.display = "none";
    }};

    var tick = function () {{

        var span = layer.querySelector(
            ".{timer_class} span"
        );

        if (span) {{
            span.textContent = remain;
        }}

        remain -= 1;

        timer =
            remain >= 0
                ? window.setTimeout(tick, 1000)
                : window.setTimeout(close, 0);
    }};

    var skip = layer.querySelector(
        ".{skip_class}"
    );

    if (skip) {{

        skip.addEventListener(
            "click",
            function (event) {{

                event.preventDefault();
                event.stopPropagation();

                close();
            }}
        );
    }}

    tick();

}})();
</script>
"""

def rewrite_ad(text):
    """
    Apply stable, type-specific advertisement transformations.

    Pre-roll insertion remains disabled.  Each advertisement type is filtered
    only through its own blacklist and DOM-container contract.
    """

    text = _remove_video_card_ads(text)
    text = _remove_video_list_card_ads(text)
    text = _remove_banner_image_ads(text)
    text = _remove_text_slot_ads(text)
    return text


__all__ = [
    "rewrite_ad",
]
