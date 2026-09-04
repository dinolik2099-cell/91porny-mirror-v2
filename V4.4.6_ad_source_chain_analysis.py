from pathlib import Path
from urllib.parse import urlparse
import re
from collections import defaultdict

SRC = Path("analysis/stage6/stage6_6/r6_4_3/r5/video.html")

CANDIDATES = [
    "https://zgq0wua9ha6cdp2xc.yjxsxh.com/1_mfdy/dp7/index.html?channelCode=mfd024",
    "https://vluydzksoneb.xn--e-q07as6t.com:9595/?blt021",
    "https://c710ne6.5084602.top:5088/facai.html?xm8050-2",
    "https://99pg628.99211764.com:507/ad88.html?pg6007#pg6007",
    "https://toptvbnw.i6z7t5.com/1Aj.html",
    "https://613t.8327114.cc/",
    "https://737d.7370179.cc/",
    "https://908b.8424133.cc/",
    "https://psuu.bahwhr.cc/",
    "https://www.by2599.cc/",
]

if not SRC.exists():
    raise SystemExit(f"ERROR: source not found: {SRC}")

html = SRC.read_text(encoding="utf-8", errors="ignore")

print("=" * 88)
print("V4.4.6 广告 / 分发候选本地来源链分析")
print("=" * 88)
print(f"SRC={SRC}")
print(f"HTML_BYTES={len(html.encode('utf-8'))}")
print(f"CANDIDATE_COUNT={len(CANDIDATES)}")
print("MODE=STATIC_ONLY")
print("URL_ACCESS=0")
print("HTTP_REQUEST=0")
print("NAVIGATION=0")
print("DOWNLOAD=0")
print("JS_EXECUTION=0")
print("THIRD_PARTY_ACCESS=0")
print()

def normalize_space(s):
    return re.sub(r"\s+", " ", s).strip()

def context_for(pos, radius=700):
    start = max(0, pos - radius)
    end = min(len(html), pos + radius)
    return normalize_space(html[start:end])

def structural_signature(ctx):
    sig = []

    if 'target="_blank"' in ctx or "target='_blank'" in ctx:
        sig.append("TARGET_BLANK")

    if "rel=\"noopener nofollow\"" in ctx or "rel='noopener nofollow'" in ctx:
        sig.append("NOOPENER_NOFOLLOW")

    if "text-danger" in ctx:
        sig.append("TEXT_DANGER")

    if "display d-block" in ctx:
        sig.append("DISPLAY_TILE")

    if "video-elem" in ctx:
        sig.append("VIDEO_ELEM")

    if "<img" in ctx:
        sig.append("IMG_ANCHOR")

    if "background-image" in ctx:
        sig.append("BACKGROUND_IMAGE")

    if "nav-link" in ctx:
        sig.append("NAV_LINK")

    if 'class="Item"' in ctx or "class='Item'" in ctx:
        sig.append("ITEM_LINK")

    if "onclick" in ctx.lower():
        sig.append("ONCLICK")

    return sig

# ----------------------------------------------------------------------
# 1. 每个候选 URL 的精确出现位置
# ----------------------------------------------------------------------

records = []

print("=" * 88)
print("1. 候选 URL → 本地 HTML 精确来源")
print("=" * 88)

for url in CANDIDATES:
    positions = [m.start() for m in re.finditer(re.escape(url), html)]

    print()
    print(f"URL={url}")
    print(f"OCCURRENCES={len(positions)}")

    for idx, pos in enumerate(positions, 1):
        ctx = context_for(pos)
        sig = structural_signature(ctx)

        print(f"  [{idx}] POS={pos}")
        print(f"      SIGNATURE={','.join(sig) if sig else 'NONE'}")
        print(f"      CONTEXT={ctx[:1200]}")

        records.append({
            "url": url,
            "host": urlparse(url).netloc,
            "path": urlparse(url).path,
            "query": urlparse(url).query,
            "pos": pos,
            "signature": tuple(sig),
            "context": ctx,
        })

# ----------------------------------------------------------------------
# 2. 从 HTML 中提取候选 URL 所在的完整 <a> 标签
# ----------------------------------------------------------------------

print()
print("=" * 88)
print("2. 提取完整 <a> 标签，判断是否存在统一模板")
print("=" * 88)

anchor_records = []

for m in re.finditer(r"<a\b[^>]*>.*?</a>", html, re.I | re.S):
    anchor = m.group(0)

    matched = [u for u in CANDIDATES if u in anchor]
    if not matched:
        continue

    clean = normalize_space(anchor)

    # 去掉过长内容，仅保留结构分析需要的部分
    if len(clean) > 1800:
        clean = clean[:1800] + "..."

    for url in matched:
        attrs = {
            "target_blank": bool(re.search(r'target\s*=\s*["\']_blank["\']', anchor, re.I)),
            "noopener": "noopener" in anchor.lower(),
            "nofollow": "nofollow" in anchor.lower(),
            "onclick": bool(re.search(r'onclick\s*=', anchor, re.I)),
            "img": bool(re.search(r"<img\b", anchor, re.I)),
            "text_danger": "text-danger" in anchor,
            "display_tile": "display d-block" in anchor,
            "nav_link": "nav-link" in anchor,
            "item": bool(re.search(r'class\s*=\s*["\'][^"\']*\bItem\b', anchor, re.I)),
        }

        anchor_records.append((url, attrs, clean))

        print()
        print(f"URL={url}")
        print(f"ATTRS={attrs}")
        print(f"A_TAG={clean}")

# ----------------------------------------------------------------------
# 3. 提取候选 URL 周围的图片资源 / 外部资源
# ----------------------------------------------------------------------

print()
print("=" * 88)
print("3. 候选 URL → 同一 HTML 结构中的图片 / 外部资源")
print("=" * 88)

resource_groups = defaultdict(set)

for url, attrs, anchor in anchor_records:
    imgs = re.findall(
        r"""(?:src|data-src|data-original|background-image)\s*=\s*["']([^"']+)["']""",
        anchor,
        re.I,
    )

    for img in imgs:
        resource_groups[url].add(img)

    bg = re.findall(
        r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""",
        anchor,
        re.I,
    )

    for item in bg:
        resource_groups[url].add(item)

for url in CANDIDATES:
    print()
    print(f"URL={url}")

    resources = sorted(resource_groups.get(url, set()))

    if not resources:
        print("  RESOURCES=NONE")
    else:
        for r in resources:
            print(f"  RESOURCE={r}")

# ----------------------------------------------------------------------
# 4. URL 参数结构分类
# ----------------------------------------------------------------------

print()
print("=" * 88)
print("4. URL 参数结构归类")
print("=" * 88)

param_groups = defaultdict(list)

for url in CANDIDATES:
    p = urlparse(url)
    query = p.query

    if "channelCode=" in query:
        family = "CHANNEL_CODE"
    elif "blt021" in query:
        family = "BLT_TOKEN"
    elif "xm8050-2" in query:
        family = "XM_TOKEN"
    elif "pg6007" in query:
        family = "PG_TOKEN"
    elif "cid=" in query:
        family = "CID"
    elif p.path.endswith(".html"):
        family = "STATIC_HTML"
    elif p.path == "/":
        family = "ROOT_PATH"
    else:
        family = "OTHER"

    param_groups[family].append(url)

for family, urls in param_groups.items():
    print()
    print(f"[{family}] COUNT={len(urls)}")
    for u in urls:
        print(f"  {u}")

# ----------------------------------------------------------------------
# 5. 结构签名归并
# ----------------------------------------------------------------------

print()
print("=" * 88)
print("5. HTML 来源结构签名归并")
print("=" * 88)

signature_groups = defaultdict(list)

for url, attrs, anchor in anchor_records:
    sig = []

    if attrs["target_blank"]:
        sig.append("TARGET_BLANK")
    if attrs["noopener"] and attrs["nofollow"]:
        sig.append("NOOPENER_NOFOLLOW")
    if attrs["text_danger"]:
        sig.append("TEXT_DANGER")
    if attrs["display_tile"]:
        sig.append("DISPLAY_TILE")
    if attrs["img"]:
        sig.append("IMG")
    if attrs["nav_link"]:
        sig.append("NAV_LINK")
    if attrs["item"]:
        sig.append("ITEM")
    if attrs["onclick"]:
        sig.append("ONCLICK")

    signature_groups[tuple(sig)].append(url)

for sig, urls in signature_groups.items():
    print()
    print(f"SIGNATURE={'+'.join(sig) if sig else 'NONE'}")
    for u in sorted(set(urls)):
        print(f"  {u}")

# ----------------------------------------------------------------------
# 6. 判断是否存在统一广告模板的本地证据
# ----------------------------------------------------------------------

print()
print("=" * 88)
print("6. 本地证据汇总")
print("=" * 88)

# 统计共同特征
all_anchor_attrs = []

for url, attrs, anchor in anchor_records:
    all_anchor_attrs.append(attrs)

def ratio(key):
    if not all_anchor_attrs:
        return 0
    return sum(1 for x in all_anchor_attrs if x[key]) / len(all_anchor_attrs)

print(f"ANCHOR_COUNT={len(anchor_records)}")
print(f"TARGET_BLANK_RATIO={ratio('target_blank'):.2f}")
print(f"NOOPENER_RATIO={ratio('noopener'):.2f}")
print(f"NOFOLLOW_RATIO={ratio('nofollow'):.2f}")
print(f"ONCLICK_RATIO={ratio('onclick'):.2f}")
print(f"IMG_RATIO={ratio('img'):.2f}")
print(f"TEXT_DANGER_RATIO={ratio('text_danger'):.2f}")

# 图片域名
img_hosts = defaultdict(int)

for url, resources in resource_groups.items():
    for r in resources:
        try:
            rp = urlparse(r)
            if rp.netloc:
                img_hosts[rp.netloc] += 1
        except Exception:
            pass

print()
print("IMAGE_RESOURCE_HOSTS:")
if img_hosts:
    for host, count in sorted(img_hosts.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {host} -> {count}")
else:
    print("  NONE")

# ----------------------------------------------------------------------
# 7. 最终阶段判断
# ----------------------------------------------------------------------

print()
print("=" * 88)
print("7. V4.4.6 阶段判断")
print("=" * 88)

print("""
本轮只回答一个问题：

这些候选 URL 在当前本地 HTML 中，
是否已经可以通过“来源结构 + 参数形式 + 广告资源”
归并为已有的静态广告 / 分发系统，而不是新的动态攻击链？

判断规则：

A. 只有普通 <a href>，无 onclick / JS 生成：
   → 静态入口候选

B. target=_blank + noopener + nofollow：
   → 强静态外链 / 广告入口信号

C. 与 img / background-image / text-danger / 广告 tile 共现：
   → 强广告模板信号

D. channelCode / blt021 / facai / ad88 / 1Aj 等参数或路径：
   → 记录为入口形态，不直接等同于攻击链

E. 只有发现本地 JS / 动态 API / 参数生成 / 跳转逻辑，
   才升级为新的“动态机制候选”。

注意：
本轮没有访问任何候选站点，
因此不能证明这些外部入口最终会执行什么。
这里只证明本地页面如何引用它们。
""")

print()
print("FINAL SAFETY STATE:")
print("MODE=STATIC_ONLY")
print("URL_ACCESS=0")
print("HTTP_REQUEST=0")
print("NAVIGATION=0")
print("DOWNLOAD=0")
print("JS_EXECUTION=0")
print("THIRD_PARTY_ACCESS=0")
print("V1_8021=UNTOUCHED")
print("V2_8022=UNTOUCHED")

print()
print("=" * 88)
print("V4.4.6 DONE")
print("=" * 88)
