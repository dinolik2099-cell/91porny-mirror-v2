from pathlib import Path
import re

ROOT = Path("/www/wwwroot/91porny")

# 我们已经确认的真实广告候选
TARGETS = [
    "18f4.com",
    "facai.html",
    "ad88.html",
    "1Aj.html",
    "channelCode=mfd024",
    "blt021",
    "613t.8327114.cc",
    "737d.7370179.cc",
    "908b.8424133.cc",
    "psuu.bahwhr.cc",
    "www.by2599.cc",
]

# 页面特征
PAGE_MARKERS = [
    "<video",
    "data-src",
    "video-play",
    "倒计时",
    "data-nosnippet",
    "text-danger",
    "target=\"_blank\"",
    "noopener",
    "nofollow",
]

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "logs",
    "tmp",
    "cache",
}

TEXT_EXTS = {
    ".html", ".htm", ".txt", ".json", ".js", ".py",
    ".xml", ".m3u8", ".yaml", ".yml", ".log"
}

print("=" * 88)
print("V4.4.7-R6 历史原始 HTML / 页面快照定位")
print("=" * 88)
print(f"ROOT={ROOT}")
print("MODE=LOCAL_EVIDENCE_DISCOVERY_ONLY")
print("URL_ACCESS=0")
print("HTTP_REQUEST=0")
print("NAVIGATION=0")
print("DOWNLOAD=0")
print("JS_EXECUTION=0")
print("THIRD_PARTY_ACCESS=0")
print("V1_8021=UNTOUCHED")
print("V2_EXECUTION=0")
print()

# ============================================================
# 1. 找候选文件
# ============================================================

print("=" * 88)
print("1. FILE_DISCOVERY")
print("=" * 88)

files = []

for p in ROOT.rglob("*"):
    if not p.is_file():
        continue

    if any(part in SKIP_DIRS for part in p.parts):
        continue

    if p.suffix.lower() not in TEXT_EXTS:
        continue

    try:
        size = p.stat().st_size
    except OSError:
        continue

    # 避免把巨型日志/数据文件全部纳入
    if size > 20 * 1024 * 1024:
        continue

    files.append(p)

print(f"TEXT_FILES={len(files)}")
print()

# ============================================================
# 2. 找包含真实广告候选的历史文件
# ============================================================

print("=" * 88)
print("2. AD_TARGET_HISTORY")
print("=" * 88)

target_file_hits = {}

for target in TARGETS:
    hits = []

    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if target.lower() in text.lower():
            hits.append(p)

    target_file_hits[target] = hits

    print()
    print(f"TARGET={target}")
    print(f"FILE_COUNT={len(hits)}")

    for p in hits[:20]:
        try:
            size = p.stat().st_size
        except OSError:
            size = -1

        print(f"  {p.relative_to(ROOT)} | SIZE={size}")

    if len(hits) > 20:
        print(f"  ... {len(hits)-20} MORE")

# ============================================================
# 3. 找真正像 HTML 页面快照的文件
# ============================================================

print()
print("=" * 88)
print("3. HTML_SNAPSHOT_CANDIDATES")
print("=" * 88)

snapshot_candidates = []

for p in files:
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    low = text.lower()

    marker_count = sum(
        1 for marker in PAGE_MARKERS
        if marker.lower() in low
    )

    target_count = sum(
        1 for target in TARGETS
        if target.lower() in low
    )

    if marker_count >= 3 and (target_count >= 1 or "<video" in low):
        snapshot_candidates.append(
            (
                p,
                marker_count,
                target_count,
                len(text),
            )
        )

snapshot_candidates.sort(
    key=lambda x: (x[2], x[1], x[3]),
    reverse=True
)

print(f"SNAPSHOT_CANDIDATE_COUNT={len(snapshot_candidates)}")

for p, marker_count, target_count, length in snapshot_candidates[:80]:
    print(
        f"{p.relative_to(ROOT)} | "
        f"MARKERS={marker_count} | "
        f"AD_TARGETS={target_count} | "
        f"CHARS={length}"
    )

# ============================================================
# 4. 精确找“广告 + 视频页面”同时存在的文件
# ============================================================

print()
print("=" * 88)
print("4. VIDEO_PAGE_WITH_AD_CANDIDATES")
print("=" * 88)

combined = []

for p, marker_count, target_count, length in snapshot_candidates:

    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    low = text.lower()

    has_video = (
        "<video" in low
        or "video-play" in low
        or "data-src" in low
    )

    has_ad = any(
        target.lower() in low
        for target in TARGETS
    )

    if has_video and has_ad:
        combined.append(
            (
                p,
                marker_count,
                target_count,
                length
            )
        )

print(f"COMBINED_COUNT={len(combined)}")

for p, marker_count, target_count, length in combined[:100]:
    print(
        f"{p.relative_to(ROOT)} | "
        f"MARKERS={marker_count} | "
        f"AD_TARGETS={target_count} | "
        f"CHARS={length}"
    )

# ============================================================
# 5. 对最有价值的文件输出上下文
# ============================================================

print()
print("=" * 88)
print("5. HIGH_VALUE_CONTEXT")
print("=" * 88)

shown = set()

# 优先 combined，其次 snapshot
priority = combined + snapshot_candidates

for item in priority:
    p = item[0]

    if p in shown:
        continue

    shown.add(p)

    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    # 找出目标首次出现的位置
    positions = []

    low = text.lower()

    for target in TARGETS:
        pos = low.find(target.lower())
        if pos >= 0:
            positions.append((pos, target))

    if not positions:
        continue

    positions.sort()

    print()
    print("-" * 88)
    print(f"FILE={p.relative_to(ROOT)}")
    print(f"SIZE={len(text)}")

    # 最多输出 3 个不同位置
    for pos, target in positions[:3]:
        start = max(0, pos - 500)
        end = min(len(text), pos + 900)

        print()
        print(f"TARGET={target}")
        print(f"POSITION={pos}")
        print("-" * 60)
        print(text[start:end].replace("\x00", " ")[:1500])
        print("-" * 60)

    if len(shown) >= 15:
        break

# ============================================================
# 6. 查找原始 / rewrite / backup 关键词
# ============================================================

print()
print("=" * 88)
print("6. RAW_ORIGIN_KEYWORDS")
print("=" * 88)

KEYWORDS = [
    "original",
    "origin",
    "raw",
    "source",
    "snapshot",
    "capture",
    "response",
    "upstream",
    "before",
    "after",
    "rewrite",
    "stage6",
    "video.html",
]

keyword_files = []

for p in files:
    name = p.name.lower()

    matched = [
        k for k in KEYWORDS
        if k in name
    ]

    if matched:
        keyword_files.append((p, matched))

print(f"KEYWORD_FILENAME_COUNT={len(keyword_files)}")

for p, matched in keyword_files[:150]:
    print(
        f"{p.relative_to(ROOT)} | "
        f"KEYWORDS={','.join(matched)}"
    )

# ============================================================
# 7. 查找是否存在成对的 before / after
# ============================================================

print()
print("=" * 88)
print("7. BEFORE_AFTER_HINTS")
print("=" * 88)

for p, matched in keyword_files:
    name = p.name.lower()

    if any(
        x in name
        for x in [
            "before",
            "after",
            "raw",
            "original",
            "rewrite",
            "snapshot"
        ]
    ):
        print(f"{p.relative_to(ROOT)}")

# ============================================================
# 8. 最终判断
# ============================================================

print()
print("=" * 88)
print("8. V4.4.7-R6 JUDGMENT")
print("=" * 88)

if combined:
    print("RESULT=FOUND_LOCAL_VIDEO_PAGE_WITH_AD_EVIDENCE")
    print()
    print("下一步优先比较这些本地文件：")
    print("原始/历史页面")
    print("        VS")
    print("V2 rewrite 后页面")
    print()
    print("如果同一广告在原始页面已经存在：")
    print("=> 广告来源位于 V2 之前。")
    print()
    print("如果原始页面没有、rewrite 后出现：")
    print("=> 继续定位 V2 rewrite 注入点。")
else:
    print("RESULT=NO_DIRECT_BEFORE_AFTER_PAIR_FOUND")
    print()
    print("当前本地证据尚不足以完成原始 HTML / rewrite 前后差异验证。")
    print("下一步需要继续定位历史抓取结果、备份页面或运行日志。")

print()
print("=" * 88)
print("FINAL SAFETY STATE")
print("=" * 88)
print("MODE=LOCAL_EVIDENCE_DISCOVERY_ONLY")
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
print("V4.4.7-R6 DONE")
print("=" * 88)
