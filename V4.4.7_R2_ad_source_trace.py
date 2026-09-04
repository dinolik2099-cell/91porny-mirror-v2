from pathlib import Path
import re
from collections import defaultdict

ROOT = Path("/www/wwwroot/91porny")

# 只检查实际运行源码，绝不扫描历史 analysis
SCAN_ROOTS = [
    ROOT / "mirror",
    ROOT / "template",
]

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

EXTS = {
    ".php", ".html", ".htm", ".js", ".mjs",
    ".json", ".yaml", ".yml", ".ini", ".conf",
    ".tpl", ".txt"
}

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules",
    ".venv", "venv", "cache", "logs", "tmp"
}

MAX_SIZE = 8 * 1024 * 1024


def rel(path):
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


print("=" * 80)
print("V4.4.7-R2 广告注入源追踪")
print("=" * 80)
print("MODE=RUNTIME_SOURCE_ONLY")
print("SCAN_ROOTS=mirror,template")
print("EXCLUDE=analysis,logs,cache,tmp,.git,node_modules,venv")
print("URL_ACCESS=0")
print("HTTP_REQUEST=0")
print("NAVIGATION=0")
print("DOWNLOAD=0")
print("JS_EXECUTION=0")
print("THIRD_PARTY_ACCESS=0")
print("V1_8021=UNTOUCHED")
print("V2_8022=UNTOUCHED")
print()

# ----------------------------------------------------------------------
# 1. 建立实际源码文件列表
# ----------------------------------------------------------------------

files = []

for base in SCAN_ROOTS:
    if not base.exists():
        continue

    for p in base.rglob("*"):
        if not p.is_file():
            continue

        if any(x in SKIP_DIRS for x in p.parts):
            continue

        if p.suffix.lower() not in EXTS:
            continue

        try:
            if p.stat().st_size > MAX_SIZE:
                continue
        except OSError:
            continue

        files.append(p)

print(f"SOURCE_FILES={len(files)}")
print()

# ----------------------------------------------------------------------
# 2. 精确寻找候选 URL / 参数
# ----------------------------------------------------------------------

hits = defaultdict(list)

for p in files:
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    lines = text.splitlines()

    for n, line in enumerate(lines, 1):
        low = line.lower()

        for target in TARGETS:
            if target.lower() in low:
                hits[target].append(
                    (rel(p), n, line.strip())
                )

print("=" * 80)
print("1. 运行源码中的直接命中")
print("=" * 80)

for target in TARGETS:
    items = hits.get(target, [])

    print()
    print(f"{target} -> {len(items)}")

    if not items:
        print("  NO_DIRECT_SOURCE_MATCH")
        continue

    # 去掉完全重复的 path/line/内容
    seen = set()

    for path, line_no, text in items:
        key = (path, line_no, text)
        if key in seen:
            continue

        seen.add(key)

        # 单行最多显示 500 字符
        print(f"  {path}:{line_no} | {text[:500]}")

        if len(seen) >= 12:
            remain = len(items) - len(seen)
            if remain > 0:
                print(f"  ... {remain} more")
            break

# ----------------------------------------------------------------------
# 3. 搜索广告结构，而不是历史文件
# ----------------------------------------------------------------------

PATTERNS = {
    "channelCode": r"channelCode\s*=",
    "blt": r"\bblt\d+",
    "facai": r"facai\.html",
    "ad88": r"ad88\.html",
    "1Aj": r"1Aj\.html",
    "target_blank": r'target\s*=\s*["\']_blank["\']',
    "noopener": r"noopener",
    "nofollow": r"nofollow",
    "text_danger": r"text-danger",
    "video_elem": r"video-elem",
    "display_block": r"display\s+d-block",
}

print()
print("=" * 80)
print("2. 运行源码中的广告结构特征")
print("=" * 80)

pattern_file_hits = defaultdict(set)
pattern_counts = defaultdict(int)

for p in files:
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    for name, pattern in PATTERNS.items():
        count = len(re.findall(pattern, text, re.I))

        if count:
            pattern_counts[name] += count
            pattern_file_hits[name].add(rel(p))

for name in PATTERNS:
    print(
        f"{name}: "
        f"COUNT={pattern_counts[name]} "
        f"FILES={len(pattern_file_hits[name])}"
    )

# ----------------------------------------------------------------------
# 4. 找最可能的“广告注入源码文件”
# ----------------------------------------------------------------------

print()
print("=" * 80)
print("3. 候选广告注入源码文件")
print("=" * 80)

scores = []

for p in files:
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    score = 0
    reasons = []

    checks = [
        ("channelCode", r"channelCode\s*="),
        ("blt", r"\bblt\d+"),
        ("facai", r"facai\.html"),
        ("ad88", r"ad88\.html"),
        ("1Aj", r"1Aj\.html"),
        ("广告结构", r"text-danger"),
        ("广告结构", r"target\s*=\s*[\"']_blank"),
        ("广告结构", r"noopener"),
        ("广告结构", r"nofollow"),
    ]

    for label, pattern in checks:
        if re.search(pattern, text, re.I):
            score += 1
            if label not in reasons:
                reasons.append(label)

    if score:
        scores.append((score, rel(p), reasons))

scores.sort(key=lambda x: (-x[0], x[1]))

if not scores:
    print("NO_RUNTIME_AD_SOURCE_CANDIDATE")
else:
    for score, path, reasons in scores[:30]:
        print(
            f"SCORE={score} "
            f"FILE={path} "
            f"REASONS={','.join(reasons)}"
        )

# ----------------------------------------------------------------------
# 5. 判断候选是否由 JS 动态生成
# ----------------------------------------------------------------------

print()
print("=" * 80)
print("4. 动态生成迹象")
print("=" * 80)

DYNAMIC_PATTERNS = [
    r"location\s*\.",
    r"window\s*\.\s*location",
    r"location\s*=",
    r"location\.href",
    r"location\.replace",
    r"location\.assign",
    r"window\.open",
    r"createElement\s*\(\s*[\"']a",
    r"setAttribute\s*\(\s*[\"']href",
    r"\.href\s*=",
    r"innerHTML\s*=",
    r"document\.write",
    r"fetch\s*\(",
    r"XMLHttpRequest",
    r"\$\.ajax",
    r"\$\.get\s*\(",
    r"\$\.post\s*\(",
]

dynamic_hits = []

for p in files:
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    matched = []

    for pattern in DYNAMIC_PATTERNS:
        if re.search(pattern, text, re.I):
            matched.append(pattern)

    if matched:
        dynamic_hits.append((rel(p), matched))

if not dynamic_hits:
    print("DYNAMIC_GENERATION_SOURCE_MATCH=0")
else:
    print(f"DYNAMIC_SOURCE_FILES={len(dynamic_hits)}")

    for path, matched in dynamic_hits[:30]:
        print(f"  {path}")
        print(f"    SIGNALS={len(matched)}")

# ----------------------------------------------------------------------
# 6. 最终结论
# ----------------------------------------------------------------------

print()
print("=" * 80)
print("5. V4.4.7-R2 结论")
print("=" * 80)

direct_count = sum(len(v) for v in hits.values())

print(f"RUNTIME_SOURCE_FILES={len(files)}")
print(f"DIRECT_TARGET_MATCHES={direct_count}")
print(f"DYNAMIC_SOURCE_FILES={len(dynamic_hits)}")

print()
print("解释：")

if direct_count:
    print("1. 至少部分广告 URL / 参数可以在实际运行源码中找到。")
    print("   → 继续判断其是否来自统一模板 / 配置。")
else:
    print("1. 实际运行源码中没有直接发现候选 URL / 参数。")
    print("   → 候选可能来自数据库、运行时数据或上游生成结果。")

if dynamic_hits:
    print("2. 实际运行源码存在动态跳转/URL生成相关代码。")
    print("   → 需要进一步区分这些代码是否真正作用于广告候选。")
else:
    print("2. 实际运行源码没有发现明显动态广告跳转生成代码。")

print()
print("本轮明确不做：")
print("- 不访问任何外部域名")
print("- 不执行第三方 JS")
print("- 不点击广告")
print("- 不下载资源")
print("- 不修改 V1")
print("- 不修改 V2")
print("- 不修改 Nginx / BTWAF")

print()
print("=" * 80)
print("FINAL SAFETY STATE")
print("=" * 80)
print("MODE=RUNTIME_SOURCE_ONLY")
print("URL_ACCESS=0")
print("HTTP_REQUEST=0")
print("NAVIGATION=0")
print("DOWNLOAD=0")
print("JS_EXECUTION=0")
print("THIRD_PARTY_ACCESS=0")
print("V1_8021=UNTOUCHED")
print("V2_8022=UNTOUCHED")

print()
print("=" * 80)
print("V4.4.7-R2 DONE")
print("=" * 80)
