#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V4.4.4
16 个 UNKNOWN 外部 Anchor 静态结构分类

只读取：
analysis/stage6/stage6_6/r6_4_3/r5/video.html

安全限制：
- 不访问 UNKNOWN URL
- 不发送 HTTP 请求
- 不导航
- 不下载
- 不执行第三方 JS
- 不修改 V1 / 8021
- 不修改 V2 / 8022
"""

import re
from pathlib import Path
from urllib.parse import urlparse, parse_qsl
from collections import defaultdict


# ============================================================
# 输入文件
# ============================================================

SRC = Path(
    "analysis/stage6/stage6_6/r6_4_3/r5/video.html"
)


# ============================================================
# V4.4.3 已知资源
# ============================================================

KNOWN_HOSTS = {
    "65.jj10605.vip",
    "s27ecl.jt46333.cc",
    "lbs10-893927144.ap-east-1.elb.amazonaws.com",
    "google.com",
    "www.google.com",
    "google-analytics.com",
    "www.google-analytics.com",
    "googletagmanager.com",
    "www.googletagmanager.com",
    "fastly.jsdelivr.net",
    "img.alicdn.com",
}

KNOWN_HOST_KEYWORDS = {
    "schema.org",
    "cloudfront.net",
}

MEDIA_KEYWORDS = {
    "m3u8",
    ".ts",
    "jiuse",
}

IMAGE_KEYWORDS = {
    "ucloud",
    "qiniu",
}


# ============================================================
# TEST_02 / TEST_03 已知结构
# ============================================================

def detect_known_family(info):
    host = info["hostname"]
    path = info["path"].lower()
    query_keys = info["query_keys"]

    # TEST_02：65J_D65
    if host == "65.jj10605.vip":
        return "TEST_02 / 65J_D65"

    # TEST_02：OpenShare / LBS
    if "elb.amazonaws.com" in host:
        return "TEST_02 / OpenShare-LBS"

    # TEST_03：88.html + cid
    if path.endswith("/88.html") and "cid" in query_keys:
        return "TEST_03 / 88.html + cid"

    # TEST_03 同类 cid 入口
    if "cid" in query_keys:
        return "TEST_03 同类 / cid 参数"

    return None


# ============================================================
# 提取 Anchor href
# ============================================================

def extract_hrefs(html):
    pattern = re.compile(
        r'<a\b[^>]*?\bhref\s*=\s*'
        r'(["\'])(.*?)\1',
        re.IGNORECASE | re.DOTALL
    )

    result = []

    for _, href in pattern.findall(html):
        href = href.strip()

        if not href:
            continue

        if href.startswith("//"):
            href = "https:" + href

        if href.startswith(("http://", "https://")):
            result.append(href)

    return result


# ============================================================
# URL 解析
# ============================================================

def parse_url(url):

    p = urlparse(url)

    hostname = (p.hostname or "").lower()
    netloc = (p.netloc or "").lower()

    try:
        port = p.port
    except ValueError:
        port = "INVALID"

    path = p.path or "/"

    query_pairs = parse_qsl(
        p.query,
        keep_blank_values=True
    )

    query_keys = sorted({
        key.lower()
        for key, _ in query_pairs
    })

    query_values = {
        key.lower(): value
        for key, value in query_pairs
    }

    segments = [
        x for x in path.split("/")
        if x
    ]

    filename = (
        segments[-1].lower()
        if segments
        else ""
    )

    if path == "/":
        path_type = "ROOT"
    elif path.lower().endswith(".html"):
        path_type = "HTML"
    elif path.lower().endswith(".php"):
        path_type = "PHP"
    else:
        path_type = "DIRECTORY_OTHER"

    return {
        "url": url,
        "hostname": hostname,
        "host": netloc,
        "port": port,
        "path": path,
        "segments": segments,
        "depth": len(segments),
        "filename": filename,
        "path_type": path_type,
        "query_keys": query_keys,
        "query_values": query_values,
        "query_count": len(query_pairs),
    }


# ============================================================
# 判断是否为 UNKNOWN
# ============================================================

def is_unknown(info):

    hostname = info["hostname"]
    path = info["path"].lower()

    if hostname in KNOWN_HOSTS:
        return False

    for keyword in KNOWN_HOST_KEYWORDS:
        if keyword in hostname:
            return False

    for keyword in MEDIA_KEYWORDS:
        if keyword in hostname or keyword in path:
            return False

    for keyword in IMAGE_KEYWORDS:
        if keyword in hostname or keyword in path:
            return False

    return True


# ============================================================
# 结构分类
# ============================================================

def classify(info):

    known = detect_known_family(info)

    if known:
        return known

    host = info["hostname"]
    path = info["path"].lower()
    filename = info["filename"]
    query_keys = info["query_keys"]
    port = info["port"]

    # 占位域
    if host == "example.invalid":
        return "非真实资源 / example.invalid"

    # --------------------------------------------------------
    # 新家族候选 A：join/token
    # --------------------------------------------------------

    if "/join/" in path:
        return "新家族候选 A / join-token"

    # --------------------------------------------------------
    # 新家族候选 B：facai
    # --------------------------------------------------------

    if "facai.html" in path:
        return "新家族候选 B / facai.html"

    # --------------------------------------------------------
    # 新家族候选 C：laicai
    # --------------------------------------------------------

    if "laicai.html" in path:
        return "新家族候选 C / laicai.html"

    # --------------------------------------------------------
    # 新家族候选 D：ad88
    # --------------------------------------------------------

    if "ad88.html" in path:
        return "新家族候选 D / ad88.html"

    # --------------------------------------------------------
    # 新家族候选 E：channelCode
    # --------------------------------------------------------

    if "channelcode" in query_keys:
        return "新家族候选 E / channelCode 分发"

    # --------------------------------------------------------
    # 新家族候选 F：非标准端口
    # --------------------------------------------------------

    if port not in (None, 80, 443, "INVALID"):
        return "新家族候选 F / 非标准端口"

    # --------------------------------------------------------
    # 新家族候选 G：根路径
    # --------------------------------------------------------

    if path == "/":
        return "新家族候选 G / 根路径入口"

    # --------------------------------------------------------
    # 新家族候选 H：特殊 HTML
    # --------------------------------------------------------

    if filename.endswith(".html"):
        return "新家族候选 H / 特殊 HTML 入口"

    # --------------------------------------------------------
    # 新家族候选 I：深层目录
    # --------------------------------------------------------

    if info["depth"] >= 3:
        return "新家族候选 I / 深层目录入口"

    return "未知结构 / 待进一步分析"


# ============================================================
# 结构指纹
# ============================================================

def make_fingerprint(info):

    query = (
        ",".join(info["query_keys"])
        if info["query_keys"]
        else "NONE"
    )

    port = (
        str(info["port"])
        if info["port"]
        else "DEFAULT"
    )

    filename = (
        info["filename"]
        if info["filename"]
        else "NONE"
    )

    return (
        f"PATH_TYPE={info['path_type']} | "
        f"DEPTH={info['depth']} | "
        f"FILENAME={filename} | "
        f"QUERY_KEYS={query} | "
        f"PORT={port}"
    )


# ============================================================
# URL 结构聚类
# ============================================================

def cluster_key(info):

    return (
        info["path_type"],
        info["depth"],
        info["filename"],
        tuple(info["query_keys"]),
        info["port"] not in (None, 80, 443),
    )


# ============================================================
# 主程序
# ============================================================

def main():

    print()
    print("=" * 72)
    print("V4.4.4 UNKNOWN 外部链接静态结构分类")
    print("=" * 72)

    print()
    print(f"SRC={SRC}")

    if not SRC.exists():
        print()
        print("ERROR: 输入文件不存在")
        print(f"请确认文件：{SRC}")
        print()
        return

    # --------------------------------------------------------
    # 读取本地 HTML
    # --------------------------------------------------------

    html = SRC.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    hrefs = extract_hrefs(html)
    unique_hrefs = sorted(set(hrefs))

    print()
    print(f"ANCHOR_HREFS={len(hrefs)}")
    print(f"UNIQUE_EXTERNAL={len(unique_hrefs)}")

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    unknown = []

    for url in unique_hrefs:
        info = parse_url(url)

        if is_unknown(info):
            unknown.append(info)

    print()
    print("=" * 72)
    print("一、UNKNOWN 总量")
    print("=" * 72)
    print()
    print(f"UNKNOWN_COUNT={len(unknown)}")

    # --------------------------------------------------------
    # 分类
    # --------------------------------------------------------

    for info in unknown:
        info["family"] = classify(info)
        info["fingerprint"] = make_fingerprint(info)

    # --------------------------------------------------------
    # 逐条结构分析
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("二、UNKNOWN 逐条结构分析")
    print("=" * 72)

    for index, info in enumerate(unknown, 1):

        print()
        print(f"[UNKNOWN_{index:02d}]")
        print(f"URL={info['url']}")
        print(f"FAMILY={info['family']}")
        print(f"HOST={info['host']}")

        print(
            "PORT="
            + (
                str(info["port"])
                if info["port"]
                else "DEFAULT"
            )
        )

        print(f"PATH={info['path']}")
        print(f"PATH_TYPE={info['path_type']}")
        print(f"PATH_DEPTH={info['depth']}")

        print(
            "FILENAME="
            + (
                info["filename"]
                if info["filename"]
                else "NONE"
            )
        )

        print(
            "QUERY_KEYS="
            + (
                ",".join(info["query_keys"])
                if info["query_keys"]
                else "NONE"
            )
        )

        print(
            f"QUERY_COUNT={info['query_count']}"
        )

        print(
            f"FINGERPRINT={info['fingerprint']}"
        )

    # --------------------------------------------------------
    # 逻辑家族聚类
    # --------------------------------------------------------

    families = defaultdict(list)

    for info in unknown:
        families[info["family"]].append(info)

    print()
    print("=" * 72)
    print("三、逻辑家族聚类")
    print("=" * 72)

    for family, items in sorted(
        families.items(),
        key=lambda x: (-len(x[1]), x[0])
    ):

        print()
        print(f"FAMILY={family}")
        print(f"COUNT={len(items)}")

        for item in items:
            print(f"  - {item['url']}")

    # --------------------------------------------------------
    # URL 结构聚类
    # --------------------------------------------------------

    clusters = defaultdict(list)

    for info in unknown:
        clusters[cluster_key(info)].append(info)

    print()
    print("=" * 72)
    print("四、纯 URL 结构聚类")
    print("=" * 72)

    cluster_no = 0

    for key, items in sorted(
        clusters.items(),
        key=lambda x: (-len(x[1]), str(x[0]))
    ):

        cluster_no += 1

        sample = items[0]

        print()
        print(
            f"STRUCTURE_CLUSTER_{cluster_no:02d}"
        )
        print(f"COUNT={len(items)}")
        print(
            f"STRUCTURE={sample['fingerprint']}"
        )

        for item in items:
            print(f"  - {item['url']}")

    # --------------------------------------------------------
    # 已验证家族重复项
    # --------------------------------------------------------

    known_repeat = [
        info
        for info in unknown
        if (
            info["family"].startswith("TEST_02")
            or info["family"].startswith("TEST_03")
        )
    ]

    print()
    print("=" * 72)
    print("五、已验证家族重复项")
    print("=" * 72)

    if known_repeat:

        for info in known_repeat:

            print()
            print(
                f"SKIP_REPEAT={info['url']}"
            )
            print(
                f"REASON={info['family']}"
            )

    else:
        print("无明显 TEST_02 / TEST_03 重复项。")

    # --------------------------------------------------------
    # 新家族首次验证候选
    # --------------------------------------------------------

    candidate_families = defaultdict(list)

    for info in unknown:

        family = info["family"]

        if (
            family.startswith("新家族候选")
            or family.startswith("未知结构")
        ):
            candidate_families[family].append(info)

    print()
    print("=" * 72)
    print("六、首次验证优先候选")
    print("=" * 72)

    if not candidate_families:

        print()
        print("当前没有发现新的候选家族。")

    else:

        priority_no = 0

        for family, items in sorted(
            candidate_families.items(),
            key=lambda x: x[0]
        ):

            priority_no += 1

            representative = items[0]

            print()
            print(
                f"PRIORITY_{priority_no:02d}"
            )

            print(
                f"FAMILY={family}"
            )

            print(
                f"REPRESENTATIVE="
                f"{representative['url']}"
            )

            print(
                f"STRUCTURE="
                f"{representative['fingerprint']}"
            )

            print(
                f"FAMILY_MEMBER_COUNT="
                f"{len(items)}"
            )

            if len(items) > 1:

                print("OTHER_MEMBERS=")

                for other in items[1:]:
                    print(
                        f"  - {other['url']}"
                    )

    # --------------------------------------------------------
    # 执行状态
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("七、执行状态")
    print("=" * 72)

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
    print("STATUS=COMPLETE")
    print("=" * 72)
    print()


if __name__ == "__main__":
    main()
