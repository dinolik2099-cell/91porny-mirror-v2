#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V4.4.5
UNKNOWN 候选 URL HTML 来源上下文追踪

目的：
    对 V4.4.4 筛出的候选 URL，
    在已有 video.html 中追踪其 HTML 来源上下文。

分析：
    - URL 出现位置
    - 所在 <a> 完整标签
    - href
    - class
    - id
    - target
    - rel
    - onclick
    - 外层 HTML 上下文
    - 相邻 HTML
    - 是否存在相同结构 URL
    - 是否可能来自同一个模板组件

严格限制：
    - 只读取本地 video.html
    - 不访问 URL
    - 不发送 HTTP 请求
    - 不导航
    - 不下载
    - 不执行 JS
    - 不修改 V1 / 8021
    - 不修改 V2 / 8022
"""

import re
from pathlib import Path
from collections import defaultdict


# ============================================================
# 输入文件
# ============================================================

SRC = Path(
    "analysis/stage6/stage6_6/r6_4_3/r5/video.html"
)


# ============================================================
# V4.4.4 候选 URL
# ============================================================

CANDIDATES = [
    "https://18f4.com/join/I1AI0owXP2ns",

    "https://c710ne6.5084602.top:5088/facai.html?xm8050-2",

    "https://99pg628.99211764.com:507/ad88.html?pg6007#pg6007",

    "https://zgq0wua9ha6cdp2xc.yjxsxh.com/1_mfdy/dp7/index.html?channelCode=mfd024",

    "https://vluydzksoneb.xn--e-q07as6t.com:9595/?blt021",

    "https://613t.8327114.cc/",
    "https://737d.7370179.cc/",
    "https://908b.8424133.cc/",
    "https://psuu.bahwhr.cc/",
    "https://www.by2599.cc/",

    "https://toptvbnw.i6z7t5.com/1Aj.html",
]


# ============================================================
# 配置
# ============================================================

CONTEXT_CHARS = 700
ANCHOR_CONTEXT_CHARS = 1200
PARENT_CONTEXT_CHARS = 1800


# ============================================================
# HTML 工具
# ============================================================

def normalize_space(text):
    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def shorten(text, max_len=1000):

    text = normalize_space(text)

    if len(text) <= max_len:
        return text

    return text[:max_len] + " ...[截断]"


# ============================================================
# 提取 URL 出现位置
# ============================================================

def find_occurrences(html, target):

    positions = []

    start = 0

    while True:

        pos = html.find(
            target,
            start
        )

        if pos == -1:
            break

        positions.append(pos)

        start = pos + len(target)

    return positions


# ============================================================
# 提取所在 Anchor
# ============================================================

def extract_anchor(html, position):

    """
    根据 URL 出现位置，向前找最近的 <a，
    向后找对应的 </a>。
    """

    left = html.rfind(
        "<a",
        0,
        position
    )

    right = html.find(
        "</a>",
        position
    )

    if left == -1 or right == -1:
        return None

    right += len("</a>")

    anchor = html[left:right]

    # 避免跨越非常大的 HTML 区域
    if len(anchor) > 30000:
        return None

    return {
        "start": left,
        "end": right,
        "html": anchor,
    }


# ============================================================
# 提取 Anchor 属性
# ============================================================

def parse_anchor_attributes(anchor):

    attrs = {}

    # href
    m = re.search(
        r'\bhref\s*=\s*([\'"])(.*?)\1',
        anchor,
        re.I | re.S
    )

    attrs["href"] = (
        m.group(2).strip()
        if m
        else None
    )

    # 常规属性
    for name in [
        "class",
        "id",
        "target",
        "rel",
        "onclick",
        "title",
        "name",
    ]:

        pattern = (
            r'\b'
            + re.escape(name)
            + r'\s*=\s*'
            r'([\'"])(.*?)\1'
        )

        m = re.search(
            pattern,
            anchor,
            re.I | re.S
        )

        attrs[name] = (
            normalize_space(m.group(2))
            if m
            else None
        )

    return attrs


# ============================================================
# HTML 上下文
# ============================================================

def get_context(
    html,
    start,
    end,
    chars
):

    left = max(
        0,
        start - chars
    )

    right = min(
        len(html),
        end + chars
    )

    return html[left:right]


# ============================================================
# 推测父级结构
# ============================================================

def find_parent_context(
    html,
    anchor_start
):

    """
    纯文本静态近似分析。

    向前寻找最近的：
        <li
        <div
        <td
        <section
        <article

    再截取一定范围。

    不做 HTML DOM 执行。
    """

    tags = [
        "<li",
        "<div",
        "<td",
        "<section",
        "<article",
        "<nav",
        "<header",
        "<footer",
    ]

    candidates = []

    for tag in tags:

        pos = html.rfind(
            tag,
            0,
            anchor_start
        )

        if pos != -1:
            candidates.append(pos)

    if not candidates:
        return None

    parent_start = max(candidates)

    parent_end = html.find(
        ">",
        parent_start
    )

    if parent_end == -1:
        return None

    parent_end += 1

    # 尝试找对应闭合标签
    tag_match = re.match(
        r"<([a-zA-Z0-9]+)",
        html[parent_start:]
    )

    if not tag_match:
        return get_context(
            html,
            parent_start,
            anchor_start,
            PARENT_CONTEXT_CHARS
        )

    tag_name = tag_match.group(1).lower()

    close_tag = (
        "</"
        + tag_name
        + ">"
    )

    close_pos = html.find(
        close_tag,
        anchor_start
    )

    if (
        close_pos != -1
        and close_pos - parent_start < 20000
    ):
        parent_end = close_pos + len(close_tag)

    else:
        parent_end = min(
            len(html),
            anchor_start + PARENT_CONTEXT_CHARS
        )

    return html[
        parent_start:parent_end
    ]


# ============================================================
# URL 结构签名
# ============================================================

def structure_signature(url):

    from urllib.parse import urlparse, parse_qsl

    p = urlparse(url)

    path = p.path or "/"

    segments = [
        x for x in path.split("/")
        if x
    ]

    filename = (
        segments[-1].lower()
        if segments
        else ""
    )

    query_keys = sorted({
        k.lower()
        for k, _ in parse_qsl(
            p.query,
            keep_blank_values=True
        )
    })

    return (
        f"PATH={path} | "
        f"DEPTH={len(segments)} | "
        f"FILE={filename or 'NONE'} | "
        f"QUERY={','.join(query_keys) or 'NONE'} | "
        f"PORT={p.port or 'DEFAULT'}"
    )


# ============================================================
# 主程序
# ============================================================

def main():

    print()
    print("=" * 78)
    print("V4.4.5 UNKNOWN 候选 URL HTML 来源上下文追踪")
    print("=" * 78)

    print()
    print(f"SRC={SRC}")

    if not SRC.exists():

        print()
        print("ERROR: 输入文件不存在")
        print(f"FILE={SRC}")
        print()

        return

    # --------------------------------------------------------
    # 读取本地 HTML
    # --------------------------------------------------------

    html = SRC.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    print()
    print(f"HTML_BYTES={len(html.encode('utf-8'))}")
    print(f"CANDIDATE_COUNT={len(CANDIDATES)}")

    # --------------------------------------------------------
    # 结果保存
    # --------------------------------------------------------

    all_results = []

    # ========================================================
    # 每个候选 URL
    # ========================================================

    for index, url in enumerate(
        CANDIDATES,
        1
    ):

        positions = find_occurrences(
            html,
            url
        )

        result = {
            "url": url,
            "positions": positions,
            "occurrences": [],
        }

        print()
        print("=" * 78)
        print(
            f"CANDIDATE_{index:02d}"
        )
        print("=" * 78)

        print()
        print(
            f"URL={url}"
        )

        print(
            f"OCCURRENCES={len(positions)}"
        )

        print(
            f"STRUCTURE="
            f"{structure_signature(url)}"
        )

        if not positions:

            print()
            print("STATUS=NOT_FOUND_IN_HTML")

            all_results.append(result)

            continue

        # ----------------------------------------------------
        # 每个出现位置
        # ----------------------------------------------------

        for occurrence_no, pos in enumerate(
            positions,
            1
        ):

            print()
            print(
                f"--- OCCURRENCE_{occurrence_no:02d} ---"
            )

            print(
                f"POSITION={pos}"
            )

            anchor_info = extract_anchor(
                html,
                pos
            )

            if anchor_info:

                anchor_html = (
                    anchor_info["html"]
                )

                attrs = parse_anchor_attributes(
                    anchor_html
                )

                print()
                print("ANCHOR_FOUND=YES")

                print(
                    f"ANCHOR_LENGTH="
                    f"{len(anchor_html)}"
                )

                print()
                print(
                    "ANCHOR_ATTRIBUTES:"
                )

                for key in [
                    "href",
                    "class",
                    "id",
                    "target",
                    "rel",
                    "onclick",
                    "title",
                    "name",
                ]:

                    value = attrs.get(key)

                    if value is None:
                        value = "NONE"

                    print(
                        f"  {key.upper()}="
                        f"{value}"
                    )

                print()
                print(
                    "ANCHOR_HTML="
                )

                print(
                    shorten(
                        anchor_html,
                        ANCHOR_CONTEXT_CHARS
                    )
                )

                parent = find_parent_context(
                    html,
                    anchor_info["start"]
                )

                if parent:

                    print()
                    print(
                        "PARENT_CONTEXT="
                    )

                    print(
                        shorten(
                            parent,
                            PARENT_CONTEXT_CHARS
                        )
                    )

                occurrence = {
                    "position": pos,
                    "anchor": anchor_html,
                    "attrs": attrs,
                    "parent": parent,
                }

            else:

                print()
                print(
                    "ANCHOR_FOUND=NO"
                )

                context = get_context(
                    html,
                    pos,
                    pos + len(url),
                    CONTEXT_CHARS
                )

                print()
                print(
                    "RAW_CONTEXT="
                )

                print(
                    shorten(
                        context,
                        CONTEXT_CHARS * 2
                    )
                )

                occurrence = {
                    "position": pos,
                    "anchor": None,
                    "attrs": {},
                    "parent": None,
                    "context": context,
                }

            result["occurrences"].append(
                occurrence
            )

        all_results.append(result)

    # ========================================================
    # 家族来源聚类
    # ========================================================

    print()
    print("=" * 78)
    print("六、候选 URL 来源结构聚类")
    print("=" * 78)

    source_groups = defaultdict(list)

    for result in all_results:

        for occurrence in result["occurrences"]:

            attrs = occurrence.get(
                "attrs",
                {}
            )

            anchor_class = (
                attrs.get("class")
                or "NONE"
            )

            anchor_id = (
                attrs.get("id")
                or "NONE"
            )

            onclick = (
                attrs.get("onclick")
                or "NONE"
            )

            key = (
                anchor_class,
                anchor_id,
                onclick,
            )

            source_groups[key].append(
                result["url"]
            )

    if source_groups:

        group_no = 0

        for key, urls in source_groups.items():

            group_no += 1

            anchor_class, anchor_id, onclick = key

            print()
            print(
                f"SOURCE_GROUP_{group_no:02d}"
            )

            print(
                f"CLASS={anchor_class}"
            )

            print(
                f"ID={anchor_id}"
            )

            print(
                f"ONCLICK={onclick}"
            )

            print(
                f"URL_COUNT={len(set(urls))}"
            )

            for url in sorted(set(urls)):
                print(
                    f"  - {url}"
                )

    else:

        print()
        print(
            "没有候选 URL 被定位到 Anchor。"
        )

    # ========================================================
    # URL → 来源结论
    # ========================================================

    print()
    print("=" * 78)
    print("七、来源判断摘要")
    print("=" * 78)

    for result in all_results:

        url = result["url"]
        occurrences = result["occurrences"]

        print()
        print(
            f"URL={url}"
        )

        if not occurrences:

            print(
                "SOURCE_STATUS="
                "HTML中未找到完整URL字符串"
            )

            continue

        anchor_count = sum(
            1
            for x in occurrences
            if x.get("anchor")
        )

        print(
            f"OCCURRENCES={len(occurrences)}"
        )

        print(
            f"ANCHOR_OCCURRENCES={anchor_count}"
        )

        if anchor_count:

            attrs_seen = []

            for occurrence in occurrences:

                attrs = occurrence.get(
                    "attrs",
                    {}
                )

                signature = (
                    attrs.get("class"),
                    attrs.get("id"),
                    attrs.get("onclick"),
                    attrs.get("target"),
                    attrs.get("rel"),
                )

                attrs_seen.append(signature)

            if len(set(attrs_seen)) == 1:

                print(
                    "SOURCE_STRUCTURE="
                    "同一 Anchor 结构"
                )

            else:

                print(
                    "SOURCE_STRUCTURE="
                    "多个 Anchor 结构"
                )

        else:

            print(
                "SOURCE_STRUCTURE="
                "URL存在但未定位到标准Anchor"
            )

    # ========================================================
    # 安全状态
    # ========================================================

    print()
    print("=" * 78)
    print("八、执行状态")
    print("=" * 78)

    print("MODE=STATIC_ONLY")
    print("LOCAL_HTML_READ=1")
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
    print("=" * 78)
    print()


if __name__ == "__main__":
    main()
