# ============================================================
# 91porny Mirror V2
# Location Rewrite
# ============================================================

SOURCE = "https://91porny.com"


def rewrite_location(value):

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
