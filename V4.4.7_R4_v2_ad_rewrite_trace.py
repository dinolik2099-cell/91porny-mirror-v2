from pathlib import Path
import re

ROOT = Path("/www/wwwroot/91porny")
V2 = ROOT / "mirror" / "mirror_v2"

TARGETS = [
    "channelCode",
    "blt021",
    "facai.html",
    "ad88.html",
    "1Aj.html",
    "613t.8327114.cc",
    "737d.7370179.cc",
    "908b.8424133.cc",
    "psuu.bahwhr.cc",
    "by2599.cc",
]

TEXT_EXTS = {
    ".py", ".js", ".json", ".yaml", ".yml",
    ".ini", ".conf", ".txt", ".html", ".htm"
}

SKIP_DIRS = {
    "__pycache__",
    ".git",
    "cache",
    "logs",
    "tmp",
}

print("=" * 88)
print("V4.4.7-R4 V2 广告 Rewrite 源码链分析")
print("=" * 88)
print(f"V2_ROOT={V2}")
print("MODE=LOCAL_SOURCE_READ_ONLY")
print("URL_ACCESS=0")
print("HTTP_REQUEST=0")
print("NAVIGATION=0")
print("DOWNLOAD=0")
print("JS_EXECUTION=0")
print("THIRD_PARTY_ACCESS=0")
print("V1_8021=UNTOUCHED")
print("V2_EXECUTION=0")
print()

if not V2.exists():
    raise SystemExit(f"V2_NOT_FOUND={V2}")

# ------------------------------------------------------------
# 1. V2 实际文件
# ------------------------------------------------------------

print("=" * 88)
print("1. V2_FILES")
print("=" * 88)

files = []

for p in sorted(V2.rglob("*"), key=lambda x: str(x)):
    if not p.is_file():
        continue

    if any(x in SKIP_DIRS for x in p.parts):
        continue

    if p.suffix.lower() not in TEXT_EXTS:
        continue

    try:
        size = p.stat().st_size
    except OSError:
        continue

    files.append(p)
    print(f"{p.relative_to(V2)} | SIZE={size}")

print(f"TEXT_FILES={len(files)}")
print()

# ------------------------------------------------------------
# 2. 读取 V2 核心源码摘要
# ------------------------------------------------------------

CORE_FILES = [
    V2 / "mirror_v2.py",
    V2 / "rewrite" / "ad.py",
    V2 / "config" / "ad_config.py",
    V2 / "core" / "proxy.py",
    V2 / "core" / "headers.py",
]

print("=" * 88)
print("2. CORE_SOURCE_STRUCTURE")
print("=" * 88)

for p in CORE_FILES:
    if not p.exists():
        print(f"NOT_FOUND={p.relative_to(ROOT)}")
        continue

    print()
    print(f"FILE={p.relative_to(ROOT)}")

    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"READ_ERROR={e}")
        continue

    lines = text.splitlines()

    print(f"LINES={len(lines)}")

    # 只输出定义 / 类 / import / URL / rewrite 相关行
    interesting = []

    patterns = [
        r"^\s*(def|async\s+def|class)\s+",
        r"import\s+",
        r"from\s+",
        r"rewrite",
        r"ad_",
        r"ad\b",
        r"url",
        r"html",
        r"response",
        r"proxy",
        r"replace",
        r"inject",
        r"template",
    ]

    for i, line in enumerate(lines, 1):
        if any(re.search(pattern, line, re.I) for pattern in patterns):
            interesting.append((i, line.strip()))

    # 去重但保留顺序
    seen = set()
    output = []

    for item in interesting:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)

    print(f"INTERESTING_LINES={len(output)}")

    for line_no, line in output[:120]:
        print(f"  {line_no}: {line[:500]}")

    if len(output) > 120:
        print(f"  ... {len(output)-120} MORE_LINES")

# ------------------------------------------------------------
# 3. V2 源码中直接搜索广告候选
# ------------------------------------------------------------

print()
print("=" * 88)
print("3. TARGET_MATCHES_IN_V2")
print("=" * 88)

target_hits = {}

for target in TARGETS:
    hits = []

    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for line_no, line in enumerate(text.splitlines(), 1):
            if target.lower() in line.lower():
                hits.append(
                    (
                        str(p.relative_to(ROOT)),
                        line_no,
                        line.strip()[:600]
                    )
                )

    target_hits[target] = hits

    print()
    print(f"TARGET={target}")
    print(f"HITS={len(hits)}")

    for path, line_no, line in hits[:15]:
        print(f"  {path}:{line_no} | {line}")

    if len(hits) > 15:
        print(f"  ... {len(hits)-15} MORE")

# ------------------------------------------------------------
# 4. 广告 URL / 外链生成相关代码
# ------------------------------------------------------------

print()
print("=" * 88)
print("4. URL_GENERATION_AND_REWRITE_SIGNALS")
print("=" * 88)

SIGNALS = [
    r"href\s*=",
    r"target\s*=",
    r"rel\s*=",
    r"replace\s*\(",
    r"re\.sub",
    r"re\.find",
    r"BeautifulSoup",
    r"bs4",
    r"lxml",
    r"select",
    r"xpath",
    r"innerHTML",
    r"createElement",
    r"window\.open",
    r"location",
    r"urljoin",
    r"urlparse",
    r"html\.replace",
    r"content\.replace",
    r"response\.text",
    r"response\.content",
]

signal_hits = []

for p in files:
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    for line_no, line in enumerate(text.splitlines(), 1):
        matched = []

        for pattern in SIGNALS:
            if re.search(pattern, line, re.I):
                matched.append(pattern)

        if matched:
            signal_hits.append(
                (
                    str(p.relative_to(ROOT)),
                    line_no,
                    matched,
                    line.strip()[:700]
                )
            )

print(f"SIGNAL_LINE_COUNT={len(signal_hits)}")

for path, line_no, matched, line in signal_hits[:120]:
    print(
        f"{path}:{line_no} "
        f"| SIGNALS={','.join(matched)} "
        f"| {line}"
    )

if len(signal_hits) > 120:
    print(f"... {len(signal_hits)-120} MORE_SIGNAL_LINES")

# ------------------------------------------------------------
# 5. ad.py 专项分析
# ------------------------------------------------------------

print()
print("=" * 88)
print("5. AD_PY_FUNCTIONS_AND_CONFIG")
print("=" * 88)

ad_py = V2 / "rewrite" / "ad.py"
ad_cfg = V2 / "config" / "ad_config.py"

for p in [ad_py, ad_cfg]:

    print()
    print(f"FILE={p.relative_to(ROOT)}")

    if not p.exists():
        print("NOT_FOUND")
        continue

    text = p.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    for i, line in enumerate(lines, 1):
        if re.search(
            r"^\s*(def|async\s+def|class)\s+|"
            r"https?://|"
            r"href|"
            r"replace|"
            r"pattern|"
            r"regex|"
            r"selector|"
            r"inject|"
            r"remove|"
            r"rewrite|"
            r"config|"
            r"enabled|"
            r"domain|"
            r"ad",
            line,
            re.I
        ):
            print(f"  {i}: {line[:700]}")

# ------------------------------------------------------------
# 6. 判断 V2 当前广告链类型
# ------------------------------------------------------------

print()
print("=" * 88)
print("6. V4.4.7-R4 PRELIMINARY JUDGMENT")
print("=" * 88)

ad_matches = sum(
    len(v)
    for k, v in target_hits.items()
    if k not in {"channelCode", "blt021"}
)

print(f"TARGET_TOTAL_HITS={sum(len(v) for v in target_hits.values())}")
print(f"AD_URL_DIRECT_HITS={ad_matches}")

if target_hits.get("channelCode"):
    print("CHANNEL_CODE_SOURCE=FOUND_IN_V2")
else:
    print("CHANNEL_CODE_SOURCE=NOT_FOUND_IN_V2")

if target_hits.get("blt021"):
    print("BLT_SOURCE=FOUND_IN_V2")
else:
    print("BLT_SOURCE=NOT_FOUND_IN_V2")

print()
print("判断原则：")
print("1. 如果候选 URL 在 V2 rewrite/ad.py 或 ad_config.py 中出现：")
print("   → V2 可能参与广告生成/改写。")
print()
print("2. 如果候选 URL 不在 V2，但存在统一 HTML rewrite 代码：")
print("   → 继续检查 rewrite 是否只是处理上游 HTML。")
print()
print("3. 如果 V2 完全没有候选 URL，而 video.html 已经包含完整广告 HTML：")
print("   → 广告很可能在 V2 之前的上游响应中已经存在。")
print()
print("4. 本轮不会因此直接认定广告来自数据库。")
print("   → 必须继续追踪上游 HTML 的来源链。")

# ------------------------------------------------------------
# 7. 安全状态
# ------------------------------------------------------------

print()
print("=" * 88)
print("FINAL SAFETY STATE")
print("=" * 88)
print("MODE=LOCAL_SOURCE_READ_ONLY")
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
print("V4.4.7-R4 DONE")
print("=" * 88)
