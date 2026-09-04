from pathlib import Path
import re

ROOT = Path("/www/wwwroot/91porny")
V2 = ROOT / "mirror" / "mirror_v2"

FILES = [
    V2 / "mirror_v2.py",
    V2 / "core" / "proxy.py",
    V2 / "core" / "fetcher.py",
    V2 / "core" / "response.py",
    V2 / "rewrite" / "html.py",
    V2 / "rewrite" / "ad.py",
    V2 / "rewrite" / "image.py",
    V2 / "rewrite" / "location.py",
]

print("=" * 88)
print("V4.4.7-R5 HTML 生成 / Fetch / Rewrite 调用链追踪")
print("=" * 88)
print(f"ROOT={ROOT}")
print(f"V2={V2}")
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

# ============================================================
# 1. 文件存在性
# ============================================================

print("=" * 88)
print("1. SOURCE_FILES")
print("=" * 88)

existing = []

for p in FILES:
    if p.exists():
        existing.append(p)
        print(f"FOUND  {p.relative_to(ROOT)}  SIZE={p.stat().st_size}")
    else:
        print(f"MISSING {p.relative_to(ROOT)}")

print()

# ============================================================
# 2. 完整函数 / 类定义
# ============================================================

print("=" * 88)
print("2. FUNCTION_AND_CLASS_DEFINITIONS")
print("=" * 88)

for p in existing:
    text = p.read_text(encoding="utf-8", errors="ignore")
    print()
    print(f"FILE={p.relative_to(ROOT)}")

    for i, line in enumerate(text.splitlines(), 1):
        if re.match(r"^\s*(async\s+)?def\s+\w+\s*\(", line):
            print(f"  DEF {i}: {line.strip()}")

        elif re.match(r"^\s*class\s+\w+", line):
            print(f"  CLASS {i}: {line.strip()}")

# ============================================================
# 3. import 关系
# ============================================================

print()
print("=" * 88)
print("3. IMPORT_GRAPH")
print("=" * 88)

for p in existing:
    text = p.read_text(encoding="utf-8", errors="ignore")

    imports = []

    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()

        if s.startswith("import ") or s.startswith("from "):
            imports.append((i, s))

    print()
    print(f"FILE={p.relative_to(ROOT)}")

    for i, s in imports:
        print(f"  {i}: {s}")

# ============================================================
# 4. 调用关系
# ============================================================

print()
print("=" * 88)
print("4. CALL_CHAIN_SIGNALS")
print("=" * 88)

CALL_PATTERNS = [
    r"\brewrite_html\s*\(",
    r"\brewrite_ad\s*\(",
    r"\brewrite_image\s*\(",
    r"\brewrite_location\s*\(",
    r"\.fetch\s*\(",
    r"\.handle\s*\(",
    r"\bsend_response\s*\(",
    r"\burlopen\s*\(",
    r"\bRequest\s*\(",
    r"\bread\s*\(",
    r"\bdecode\s*\(",
    r"\bencode\s*\(",
    r"\bre\.sub\s*\(",
    r"\.replace\s*\(",
]

for p in existing:
    text = p.read_text(encoding="utf-8", errors="ignore")

    hits = []

    for i, line in enumerate(text.splitlines(), 1):
        matched = []

        for pattern in CALL_PATTERNS:
            if re.search(pattern, line, re.I):
                matched.append(pattern)

        if matched:
            hits.append((i, matched, line.strip()))

    if not hits:
        continue

    print()
    print(f"FILE={p.relative_to(ROOT)}")

    for i, matched, line in hits:
        print(
            f"  {i}: "
            f"SIGNALS={','.join(matched)} "
            f"| {line[:700]}"
        )

# ============================================================
# 5. HTML 输入 / 输出变量追踪
# ============================================================

print()
print("=" * 88)
print("5. HTML_INPUT_OUTPUT_SIGNALS")
print("=" * 88)

HTML_PATTERNS = [
    r"\bbody\b",
    r"\btext\b",
    r"\bhtml\b",
    r"\bcontent\b",
    r"\bresponse\b",
    r"\bsource\b",
    r"\bdata\b",
    r"\bbytes\b",
    r"Content-Type",
    r"text/html",
]

for p in existing:
    text = p.read_text(encoding="utf-8", errors="ignore")

    hits = []

    for i, line in enumerate(text.splitlines(), 1):
        if any(re.search(x, line, re.I) for x in HTML_PATTERNS):
            hits.append((i, line.strip()))

    if not hits:
        continue

    print()
    print(f"FILE={p.relative_to(ROOT)}")
    print(f"HTML_RELATED_LINES={len(hits)}")

    for i, line in hits[:100]:
        print(f"  {i}: {line[:700]}")

    if len(hits) > 100:
        print(f"  ... {len(hits)-100} MORE")

# ============================================================
# 6. URL / 外链是否由 rewrite 代码主动构造
# ============================================================

print()
print("=" * 88)
print("6. URL_CONSTRUCTION_SIGNALS")
print("=" * 88)

URL_PATTERNS = [
    r"https?://",
    r"urljoin",
    r"urlparse",
    r"urlsplit",
    r"href",
    r"src\s*=",
    r"redirect",
    r"domain",
    r"host",
    r"channelCode",
    r"cid",
    r"blt",
    r"facai",
    r"ad88",
    r"1Aj",
]

for p in existing:
    text = p.read_text(encoding="utf-8", errors="ignore")

    hits = []

    for i, line in enumerate(text.splitlines(), 1):
        if any(re.search(x, line, re.I) for x in URL_PATTERNS):
            hits.append((i, line.strip()))

    if not hits:
        continue

    print()
    print(f"FILE={p.relative_to(ROOT)}")

    for i, line in hits[:100]:
        print(f"  {i}: {line[:700]}")

    if len(hits) > 100:
        print(f"  ... {len(hits)-100} MORE")

# ============================================================
# 7. rewrite/html.py 专项
# ============================================================

print()
print("=" * 88)
print("7. REWRITE_HTML_FULL")
print("=" * 88)

p = V2 / "rewrite" / "html.py"

if p.exists():
    lines = p.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines()

    for i, line in enumerate(lines, 1):
        print(f"{i:03d}: {line}")

else:
    print("NOT_FOUND")

# ============================================================
# 8. fetcher.py 专项
# ============================================================

print()
print("=" * 88)
print("8. FETCHER_FULL")
print("=" * 88)

p = V2 / "core" / "fetcher.py"

if p.exists():
    lines = p.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines()

    for i, line in enumerate(lines, 1):
        print(f"{i:03d}: {line}")

else:
    print("NOT_FOUND")

# ============================================================
# 9. 最终判断框架
# ============================================================

print()
print("=" * 88)
print("9. V4.4.7-R5 JUDGMENT FRAME")
print("=" * 88)

print("""
A. 如果 fetcher.py：
   上游 response -> body -> rewrite_html(body)

   且 rewrite_html 只是调用：
   rewrite_ad / rewrite_image / rewrite_location
   而这些模块没有真实候选广告 URL：

   => 当前 V2 没有证据证明它生成了我们发现的真实广告。

B. 如果 rewrite_html.py 存在：
   HTML 注入、数据库读取、配置读取、URL 拼接、
   外部 HTML 片段插入等逻辑：

   => 该模块进入下一轮重点追踪。

C. 如果 fetcher.py 只是原样获取上游 HTML，
   而 rewrite_html 也没有候选广告来源：

   => 真实广告 HTML 极可能已经存在于上游响应。

D. 如果上游 HTML 已经包含真实广告：
   下一步就不再追 V2 rewrite，
   而是追：
       Fetcher
         ↓
       上游 URL 如何确定
         ↓
       原始 HTML 来源
         ↓
       上游页面是否本身携带广告

注意：
本轮仍然不能把“上游”直接等同于数据库。
必须根据源码证据继续定位。
""")

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
print("V4.4.7-R5 DONE")
print("=" * 88)
