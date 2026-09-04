# ============================================================
# 91porny Mirror V2
# Media Detector
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


def is_media(path):
    path = path.lower()
    path = path.split("?", 1)[0]
    return path.endswith(MEDIA_EXTENSIONS)
