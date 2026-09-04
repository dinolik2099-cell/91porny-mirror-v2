from pathlib import Path
import re
from collections import defaultdict

ROOT = Path("/www/wwwroot/91porny")
SRC = ROOT / "analysis/stage6/stage6_6/r6_4_3/r5/video.html"

TARGETS = [
    "channelCode=mfd024",
    "blt021",
    "facai.html",
    "ad88.html",
    "1Aj.html",
    "613t.8327114.cc",
    "737d.7370179.cc",
    "908b.8424133.cc",
    "psuu.bahwhr.cc",
    "www.by2599.cc",
]

# ----------------------------------------------------------------------
# 安全规则
# ----------------------------------------------------------------------

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "cache",
    "logs",
    "tmp",
}

TEXT_EXTS = {
    ".php",
    ".html",
    ".htm",
    ".js",
    ".mjs",
    ".json",
    ".yaml",
    ".yml",
    ".ini",
    ".conf",
    ".tpl",
    ".txt",
}

MAX_FILE_SIZE = 8 * 1024 * 1024

print("=" * 96)
print("V4.4.7 广告注入源追踪")
print("=" * 96)
print(f"ROOT={ROOT}")
print(f"SRC={SRC}")
print(f"TARGET_COUNT={len(TARGETS)}")
print("MODE=LOCAL_SOURCE_TRACE_ONLY")
print("URL_ACCESS=0")
print("HTTP_REQUEST=0")
print("NAVIGATION=0")
print("DOWNLOAD=0")
print("JS_EXECUTION=0")
print("THIRD_PARTY_ACCESS=0")
print("V1_8021=UNTOUCHED")
print("V2_8022=UNTOUCHED")
print()

if not SRC.exists():
    raise SystemExit(f"ERROR: source not found: {SRC}")

html = SRC.read_text(encoding="utf-8", errors="ignore")

# ----------------------------------------------------------------------
# 1. 当前 video.html 中广告候选的父级结构
# ----------------------------------------------------------------------

print("=" * 96)
print("1. video.html 中候选广告块的父级结构")
print("=" * 96)

for target in TARGETS:
    positions = [m.start() for m in re.finditer(re.escape(target), html)]

    print()
    print(f"TARGET={target}")
    print(f"OCCURRENCES={len(positions)}")

    for i, pos in enumerate(positions, 1):
        start = max(0, pos - 1600)
        end = min(len(html), pos + 1600)
        ctx = html[start:end]

        # 提取附近的 class / id
        classes = sorted(set(re.findall(
            r'class\s*=\s*["\']([^"\']+)["\']',
            ctx,
            re.I
        )))

        ids = sorted(set(re.findall(
            r'id\s*=\s*["\']([^"\']+)["\']',
            ctx,
            re.I
        )))

        print(f"  [{i}] POS={pos}")
        print(f"      CLASSES={classes[:30]}")
        print(f"      IDS={ids[:20]}")

# ----------------------------------------------------------------------
# 2. 本地源码扫描
# ----------------------------------------------------------------------

print()
print("=" * 96)
print("2. 本地源码扫描：查找候选 URL / 参数 / 模板特征")
print("=" * 96)

files_scanned = 0
matches = []
target_hits = defaultdict(list)

for path in ROOT.rglob("*"):

    if not path.is_file():
        continue

    # 跳过排除目录
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        continue

    if any(part in EXCLUDE_DIRS for part in rel.parts):
        continue

    if path.suffix.lower() not in TEXT_EXTS:
        continue

    try:
        size = path.stat().st_size
    except OSError:
        continue

    if size > MAX_FILE_SIZE:
        continue

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    files_scanned += 1

    lines = text.splitlines()

    for line_no, line in enumerate(lines, 1):
        for target in TARGETS:
            if target.lower() in line.lower():
                item = {
                    "path": str(path.relative_to(ROOT)),
                    "line": line_no,
                    "target": target,
                    "text": line.strip()[:1000],
                }
                matches.append(item)
                target_hits[target].append(item)

print(f"FILES_SCANNED={files_scanned}")
print(f"MATCH_COUNT={len(matches)}")

for target in TARGETS:
    print()
    print(f"TARGET={target}")
    hits = target_hits.get(target, [])

    if not hits:
        print("  LOCAL_SOURCE_MATCH=0")
        continue

    print(f"  LOCAL_SOURCE_MATCH={len(hits)}")

    for item in hits[:30]:
        print(
            f"  {item['path']}:{item['line']} "
            f"| {item['text']}"
        )

    if len(hits) > 30:
        print(f"  ... {len(hits) - 30} additional matches omitted")

# ----------------------------------------------------------------------
# 3. 搜索统一广告模板特征
# ----------------------------------------------------------------------

print()
print("=" * 96)
print("3. 统一广告模板特征扫描")
print("=" * 96)

PATTERNS = {
    "TARGET_BLANK": r'target\s*=\s*["\']_blank["\']',
    "NOOPENER": r'noopener',
    "NOFOLLOW": r'nofollow',
    "TEXT_DANGER": r'text-danger',
    "VIDEO_ELEM": r'video-elem',
    "DISPLAY_BLOCK": r'display\s+d-block',
    "ALERT_WARNING": r'alert-warning',
    "ALERT_DANGER": r'alert-danger',
    "CHANNEL_CODE": r'channelCode',
    "BLT_TOKEN": r'blt\d+',
    "FACAI": r'facai\.html',
    "AD88": r'ad88\.html',
    "SPECIAL_HTML_1AJ": r'1Aj\.html',
}

pattern_files = defaultdict(set)
pattern_counts = defaultdict(int)

for path in ROOT.rglob("*"):
    if not path.is_file():
        continue

    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        continue

    if any(part in EXCLUDE_DIRS for part in rel.parts):
        continue

    if path.suffix.lower() not in TEXT_EXTS:
        continue

    try:
        if path.stat().st_size > MAX_FILE_SIZE:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    for name, pattern in PATTERNS.items():
        count = len(re.findall(pattern, text, re.I))
        if count:
            pattern_counts[name] += count
            pattern_files[name].add(str(rel))

for name in PATTERNS:
    print()
    print(f"[{name}] COUNT={pattern_counts[name]}")
    files = sorted(pattern_files.get(name, set()))

    if files:
        for f in files[:20]:
            print(f"  FILE={f}")

        if len(files) > 20:
            print(f"  ... {len(files)-20} additional files")

# ----------------------------------------------------------------------
# 4. 识别可能的广告模板 / 数据文件
# ----------------------------------------------------------------------

print()
print("=" * 96)
print("4. 可能的广告模板 / 数据文件候选")
print("=" * 96)

candidate_files = []

KEYWORDS = [
    "ad",
    "ads",
    "advert",
    "banner",
    "link",
    "links",
    "promo",
    "promotion",
    "channel",
    "redirect",
    "partner",
    "affiliate",
]

for path in ROOT.rglob("*"):
    if not path.is_file():
        continue

    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        continue

    if any(part in EXCLUDE_DIRS for part in rel.parts):
        continue

    name = path.name.lower()

    score = 0
    reasons = []

    for kw in KEYWORDS:
        if kw in name:
            score += 1
            reasons.append(kw)

    if score:
        try:
            size = path.stat().st_size
        except OSError:
            size = -1

        candidate_files.append((score, str(rel), size, reasons))

candidate_files.sort(reverse=True)

if candidate_files:
    for score, rel, size, reasons in candidate_files[:80]:
        print(
            f"SCORE={score} "
            f"FILE={rel} "
            f"SIZE={size} "
            f"NAME_HINT={','.join(reasons)}"
        )
else:
    print("CANDIDATE_FILES=0")

# ----------------------------------------------------------------------
# 5. 检查 video.html 是否存在明显“统一广告块”
# ----------------------------------------------------------------------

print()
print("=" * 96)
print("5. video.html 广告块结构归并")
print("=" * 96)

# 抓取包含候选 URL 的最近 row / block
for target in TARGETS:
    pos = html.find(target)

    if pos < 0:
        continue

    before = html[:pos]

    row_start = before.rfind('<div class="row">')
    row_end = html.find('</div> </div>', pos)

    if row_start >= 0:
        block = html[row_start:row_end if row_end >= 0 else min(len(html), pos + 2500)]

        # 统计该块中的所有 href
        hrefs = re.findall(
            r'href\s*=\s*["\']([^"\']+)["\']',
            block,
            re.I
        )

        print()
        print(f"TARGET={target}")
        print(f"ROW_START={row_start}")
        print(f"BLOCK_HREF_COUNT={len(hrefs)}")

        for href in hrefs[:20]:
            print(f"  HREF={href}")

# ----------------------------------------------------------------------
# 6. 最终判断
# ----------------------------------------------------------------------

print()
print("=" * 96)
print("6. V4.4.7 判断标准")
print("=" * 96)

print("""
本轮不判断外部站点最终行为，只判断“本站广告入口如何产生”。

重点：

1. 如果候选 URL 只存在于最终生成的 video.html，
   而源码模板中没有固定 URL：
   → 可能来自数据库 / 远程数据 / 后端注入。

2. 如果候选 URL 在 PHP / HTML / 模板中直接出现：
   → 本地静态广告配置。

3. 如果多个候选共享同一个模板文件 / PHP 文件：
   → 高概率属于统一广告注入机制。

4. 如果发现 channelCode / blt / facai / ad88 等参数
   在本地 JS/PHP 中存在生成、拼接、替换：
   → 升级为“动态广告/分发机制候选”。

5. 如果只有最终 HTML 中出现，
   且没有生成逻辑：
   → 仍保持“静态外链广告”。

6. 本轮绝不访问外部 URL。
""")

print()
print("=" * 96)
print("FINAL SAFETY STATE")
print("=" * 96)
print("MODE=LOCAL_SOURCE_TRACE_ONLY")
print("URL_ACCESS=0")
print("HTTP_REQUEST=0")
print("NAVIGATION=0")
print("DOWNLOAD=0")
print("JS_EXECUTION=0")
print("THIRD_PARTY_ACCESS=0")
print("V1_8021=UNTOUCHED")
print("V2_8022=UNTOUCHED")

print()
print("=" * 96)
print("V4.4.7 DONE")
print("=" * 96)
