from pathlib import Path
import hashlib
import re

ROOT = Path("/www/wwwroot/91porny")

FILES = {
    "A_SOURCE_VIDEO": ROOT / "analysis/stage4/source_compare/source_video.html",
    "B_ORIGINAL_PREROLL": ROOT / "analysis/stage5/stage5_9/pre_roll_ad_full_original.html",
    "C_STAGE6_R2": ROOT / "analysis/stage6/stage6_6/r2_video.html",
    "D_STAGE6_R5": ROOT / "analysis/stage6/stage6_6/r6_4_3/r5/video.html",
}

TARGETS = [
    "18f4.com",
    "facai.html",
    "ad88.html",
    "1Aj.html",
    "channelCode",
    "blt021",
    "613t.8327114.cc",
    "737d.7370179.cc",
    "908b.8424133.cc",
    "psuu.bahwhr.cc",
    "www.by2599.cc",
]

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def read_file(path):
    if not path.exists():
        return None
    return path.read_bytes()

def text(data):
    return data.decode("utf-8", errors="ignore") if data else ""

def urls(t):
    return set(re.findall(r'https?://[^\s"\'<>]+', t))

print("=" * 88)
print("V4.4.7-R7 原始 HTML → 历史页面差异定位")
print("=" * 88)
print("MODE=LOCAL_READ_ONLY")
print("URL_ACCESS=0")
print("HTTP_REQUEST=0")
print("NAVIGATION=0")
print("DOWNLOAD=0")
print("JS_EXECUTION=0")
print("THIRD_PARTY_ACCESS=0")
print("V1_8021=UNTOUCHED")
print("V2_EXECUTION=0")
print()

data_map = {}
text_map = {}

print("=" * 88)
print("1. FILE_STATUS")
print("=" * 88)

for name, path in FILES.items():
    data = read_file(path)
    data_map[name] = data
    text_map[name] = text(data)

    if data is None:
        print(f"{name}=NOT_FOUND")
        print(f"  PATH={path.relative_to(ROOT)}")
    else:
        print(f"{name}=FOUND")
        print(f"  PATH={path.relative_to(ROOT)}")
        print(f"  SIZE={len(data)}")
        print(f"  SHA256={sha256(data)}")

print()

print("=" * 88)
print("2. TARGET_PRESENCE_MATRIX")
print("=" * 88)

print(
    "TARGET".ljust(28)
    + "".join(x.center(18) for x in FILES)
)

for target in TARGETS:
    row = target.ljust(28)

    for name in FILES:
        t = text_map[name].lower()
        count = t.count(target.lower())

        if count:
            cell = f"YES({count})"
        else:
            cell = "NO"

        row += cell.center(18)

    print(row)

print()

print("=" * 88)
print("3. AD_URL_SET_COUNTS")
print("=" * 88)

url_sets = {}

for name in FILES:
    us = urls(text_map[name])
    url_sets[name] = us

    target_urls = {
        u for u in us
        if any(t.lower() in u.lower() for t in TARGETS)
    }

    print(
        f"{name}: "
        f"ALL_URLS={len(us)} "
        f"TARGET_URLS={len(target_urls)}"
    )

print()

print("=" * 88)
print("4. TARGET_URL_SET_COMPARISON")
print("=" * 88)

names = list(FILES)

for i in range(len(names)):
    for j in range(i + 1, len(names)):

        a = names[i]
        b = names[j]

        ua = {
            u for u in url_sets[a]
            if any(t.lower() in u.lower() for t in TARGETS)
        }

        ub = {
            u for u in url_sets[b]
            if any(t.lower() in u.lower() for t in TARGETS)
        }

        added = ub - ua
        removed = ua - ub
        common = ua & ub

        print(
            f"{a} -> {b} | "
            f"COMMON={len(common)} "
            f"ADDED={len(added)} "
            f"REMOVED={len(removed)}"
        )

print()

print("=" * 88)
print("5. HTML_STRUCTURE_COUNTS")
print("=" * 88)

PATTERNS = {
    "VIDEO": r"<video\b",
    "DATA_SRC": r"data-src\s*=",
    "VIDEO_PLAY": r"video-play",
    "TEXT_DANGER": r"text-danger",
    "TARGET_BLANK": r'target\s*=\s*["\']_blank',
    "NOOPENER": r"noopener",
    "NOFOLLOW": r"nofollow",
    "IFRAME": r"<iframe\b",
    "SCRIPT": r"<script\b",
    "ONCLICK": r"onclick\s*=",
}

for name in FILES:
    t = text_map[name]

    print()
    print(name)

    for label, pattern in PATTERNS.items():
        count = len(re.findall(pattern, t, re.I))
        print(f"  {label}={count}")

print()

print("=" * 88)
print("6. PREROLL_TARGET_ANALYSIS")
print("=" * 88)

PREROLL_TARGETS = [
    "mv2ad-",
    "倒计时",
    "data-nosnippet",
    "ad_config",
    "example.invalid",
]

for name in FILES:
    t = text_map[name]

    hits = []

    for target in PREROLL_TARGETS:
        count = t.lower().count(target.lower())

        if count:
            hits.append(f"{target}={count}")

    print(
        f"{name}: "
        + (", ".join(hits) if hits else "NO_MATCH")
    )

print()

print("=" * 88)
print("7. R7_CONCLUSION")
print("=" * 88)

# 自动判断真实广告候选是否在 SOURCE 中
source = text_map["A_SOURCE_VIDEO"].lower()
r2 = text_map["C_STAGE6_R2"].lower()
r5 = text_map["D_STAGE6_R5"].lower()

source_target_count = sum(
    1 for x in TARGETS
    if x.lower() in source
)

r2_target_count = sum(
    1 for x in TARGETS
    if x.lower() in r2
)

r5_target_count = sum(
    1 for x in TARGETS
    if x.lower() in r5
)

print(f"SOURCE_VIDEO_TARGET_TYPES={source_target_count}")
print(f"STAGE6_R2_TARGET_TYPES={r2_target_count}")
print(f"STAGE6_R5_TARGET_TYPES={r5_target_count}")

print()

if source_target_count > 0:
    print("RESULT=SOURCE_VIDEO_ALREADY_CONTAINS_TARGET_ADS")
    print("=> 真实广告至少在该历史 source_video.html 中已经存在。")
    print("=> V2 不是这些真实广告 URL 的唯一生成来源。")
elif r5_target_count > 0 and source_target_count == 0:
    print("RESULT=TARGET_APPEARS_AFTER_SOURCE")
    print("=> 需要继续定位中间注入/改写环节。")
else:
    print("RESULT=INCONCLUSIVE")
    print("=> 当前四个文件不足以完成来源闭环。")

print()
print("IMPORTANT:")
print("本轮只比较已有本地文件，不访问任何外部 URL。")
print("本轮不修改任何项目文件。")

print()
print("=" * 88)
print("FINAL SAFETY STATE")
print("=" * 88)
print("MODE=LOCAL_READ_ONLY")
print("URL_ACCESS=0")
print("HTTP_REQUEST=0")
print("NAVIGATION=0")
print("DOWNLOAD=0")
print("JS_EXECUTION=0")
print("THIRD_PARTY_ACCESS=0")
print("V1_8021=UNTOUCHED")
print("V2_EXECUTION=0")

print()
print("=" * 88)
print("V4.4.7-R7 DONE")
print("=" * 88)
