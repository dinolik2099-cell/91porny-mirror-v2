from pathlib import Path

ROOT = Path("/www/wwwroot/91porny")

print("=" * 80)
print("V4.4.7-R3 运行目录 / 生成链路径定位")
print("=" * 80)
print(f"ROOT={ROOT}")
print("MODE=PATH_DISCOVERY_ONLY")
print("URL_ACCESS=0")
print("HTTP_REQUEST=0")
print("NAVIGATION=0")
print("DOWNLOAD=0")
print("JS_EXECUTION=0")
print("THIRD_PARTY_ACCESS=0")
print("V1_8021=UNTOUCHED")
print("V2_8022=UNTOUCHED")
print()

# ------------------------------------------------------------
# 1. 顶层目录
# ------------------------------------------------------------

print("=" * 80)
print("1. TOP_LEVEL")
print("=" * 80)

if not ROOT.exists():
    raise SystemExit(f"ROOT_NOT_FOUND={ROOT}")

for p in sorted(ROOT.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
    try:
        if p.is_dir():
            print(f"DIR  {p.name}/")
        else:
            print(f"FILE {p.name}  SIZE={p.stat().st_size}")
    except OSError:
        print(f"UNKNOWN {p.name}")

# ------------------------------------------------------------
# 2. 查找核心运行文件
# ------------------------------------------------------------

print()
print("=" * 80)
print("2. CORE_RUNTIME_FILES")
print("=" * 80)

patterns = [
    "mirror_v1.py",
    "mirror_v2.py",
    "run.py",
    "main.py",
    "app.py",
    "server.py",
    "ad.py",
    "ad_config.py",
]

found = []

for pattern in patterns:
    matches = list(ROOT.rglob(pattern))

    if matches:
        for p in matches:
            try:
                found.append(p)
                print(f"{p.relative_to(ROOT)}  SIZE={p.stat().st_size}")
            except Exception:
                print(str(p))
    else:
        print(f"{pattern} -> NOT_FOUND")

# ------------------------------------------------------------
# 3. 找实际模板目录
# ------------------------------------------------------------

print()
print("=" * 80)
print("3. TEMPLATE_DIRECTORIES")
print("=" * 80)

template_names = {
    "template",
    "templates",
    "tpl",
    "view",
    "views",
}

template_dirs = []

for p in ROOT.rglob("*"):
    if not p.is_dir():
        continue

    if p.name.lower() in template_names:
        try:
            template_dirs.append(p)
        except Exception:
            pass

for p in sorted(template_dirs, key=lambda x: str(x)):
    print(p.relative_to(ROOT))

if not template_dirs:
    print("NO_TEMPLATE_DIRECTORY_FOUND")

# ------------------------------------------------------------
# 4. 查找 video.html / 生成结果附近文件
# ------------------------------------------------------------

print()
print("=" * 80)
print("4. VIDEO_HTML_FILES")
print("=" * 80)

video_files = []

for p in ROOT.rglob("video.html"):
    if not p.is_file():
        continue

    # 排除历史 analysis
    try:
        rel = p.relative_to(ROOT)
    except Exception:
        continue

    if rel.parts and rel.parts[0] == "analysis":
        continue

    try:
        video_files.append(p)
        print(f"{rel}  SIZE={p.stat().st_size}")
    except OSError:
        pass

if not video_files:
    print("NO_RUNTIME_VIDEO_HTML_FOUND")

# ------------------------------------------------------------
# 5. 查找可能的 HTML 生成程序
# ------------------------------------------------------------

print()
print("=" * 80)
print("5. HTML_GENERATOR_CANDIDATES")
print("=" * 80)

generator_names = [
    "render",
    "renderer",
    "template",
    "generator",
    "generate",
    "rewrite",
    "proxy",
    "mirror",
    "page",
]

generator_candidates = []

for p in ROOT.rglob("*"):
    if not p.is_file():
        continue

    try:
        rel = p.relative_to(ROOT)
    except Exception:
        continue

    if rel.parts and rel.parts[0] == "analysis":
        continue

    name = p.name.lower()

    if any(x in name for x in generator_names):
        # 只输出文件，不读内容
        try:
            size = p.stat().st_size
        except OSError:
            size = -1

        generator_candidates.append((str(rel), size))

for rel, size in sorted(generator_candidates)[:100]:
    print(f"{rel}  SIZE={size}")

print(f"GENERATOR_NAME_CANDIDATES={len(generator_candidates)}")

# ------------------------------------------------------------
# 6. 检查 mirror 目录结构，仅显示两层
# ------------------------------------------------------------

print()
print("=" * 80)
print("6. MIRROR_TREE_MAX_DEPTH_2")
print("=" * 80)

mirror = ROOT / "mirror"

if mirror.exists():
    for p in sorted(mirror.rglob("*"), key=lambda x: str(x)):
        try:
            rel = p.relative_to(mirror)
        except Exception:
            continue

        depth = len(rel.parts)

        if depth > 2:
            continue

        if p.is_dir():
            print(f"DIR  {rel}/")
        else:
            try:
                print(f"FILE {rel}  SIZE={p.stat().st_size}")
            except OSError:
                print(f"FILE {rel}")
else:
    print("mirror/ NOT_FOUND")

# ------------------------------------------------------------
# 7. 检查 template 目录结构，仅显示两层
# ------------------------------------------------------------

print()
print("=" * 80)
print("7. TEMPLATE_TREE_MAX_DEPTH_2")
print("=" * 80)

for template in template_dirs:
    print(f"[{template.relative_to(ROOT)}]")

    count = 0

    for p in sorted(template.rglob("*"), key=lambda x: str(x)):
        try:
            rel = p.relative_to(template)
        except Exception:
            continue

        if len(rel.parts) > 2:
            continue

        if p.is_dir():
            print(f"  DIR  {rel}/")
        else:
            try:
                print(f"  FILE {rel}  SIZE={p.stat().st_size}")
            except OSError:
                print(f"  FILE {rel}")

        count += 1

        if count >= 80:
            print("  ... OUTPUT_LIMIT=80")
            break

# ------------------------------------------------------------
# 8. 最终状态
# ------------------------------------------------------------

print()
print("=" * 80)
print("8. V4.4.7-R3 RESULT")
print("=" * 80)

print("本轮只定位路径，不判断广告来源。")
print("下一步根据实际运行目录决定从哪个文件继续追踪 video.html 生成链。")

print()
print("FINAL SAFETY STATE")
print("MODE=PATH_DISCOVERY_ONLY")
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
print("V4.4.7-R3 DONE")
print("=" * 80)
