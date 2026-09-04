# 91porny Mirror V2 项目上下文恢复记录

记录时间：2026-09-04

用途：将当前 91porny Mirror V2 项目上下文迁移到新的 ChatGPT / 公司 Plus 账号。以下以已经实际验证的项目状态为准；未验证内容不作为结论。

## 一、项目目标

项目：91porny Mirror V2。

当前重点是在已经验证的镜像代理、HTML 重写、媒体边界和图片链路基础上，逐步建立广告识别与处理体系。

广告处理的正确思路已经确定为：**广告链接黑名单 + 广告类型 + DOM 容器**。

不要一次性屏蔽全部广告；一个类型一个类型验证、验收。

当前第一目标：**VIDEO CARD（视频卡片区广告）**。

后续：横幅广告、文字广告位、其他首页/分类页广告，最后再处理播放页。播放页目前不做。

## 二、开发原则

1. 一个模块一个模块验收。
2. 每次修改前备份。
3. 修改后必须做 Python 语法检查、重启、curl 实际验证。
4. 不能因为修改脚本执行完就认为修改成功，必须检查实际 HTML 和日志。
5. 广告必须按类型处理，不能用某一种特殊广告 DOM 结构套全部广告。
6. 广告识别优先使用：黑名单链接、广告类型、对应容器。
7. 不依赖源站随机 CSS class 作为广告身份。
8. 不修改视频 data-src。
9. 不修改 HLS URL。
10. 不主动代理真实媒体。
11. V1 不触碰。

## 三、当前目录与运行方式

项目根目录：`/www/wwwroot/91porny/`

V2：`/www/wwwroot/91porny/mirror/mirror_v2/`

主要模块：`config/ad_config.py`、`core/fetcher.py`、`core/proxy.py`、`core/response.py`、`media/detector.py`、`media/image_route.py`、`rewrite/ad.py`、`rewrite/html.py`、`rewrite/image.py`、`rewrite/location.py`、`mirror_v2.py`。

运行模块：`mirror_v2.mirror_v2`
监听：`127.0.0.1:8022`
Python：`/www/wwwroot/MSync/venv/bin/python3`

启动命令：
```bash
cd /www/wwwroot/91porny
PYTHONPATH=/www/wwwroot/91porny/mirror \
nohup /www/wwwroot/MSync/venv/bin/python3 -u \
-m mirror_v2.mirror_v2 \
> /www/wwwroot/91porny/logs/mirror_v2.log 2>&1 &
```

## 四、已确认的 HTML 处理链路

`浏览器 → Nginx/外层 → Mirror V2 :8022 → ProxyCore.handle() → Fetcher.fetch() → rewrite_html(body) → rewrite_ad(text) → 返回 HTML`。

`proxy.py` 已确认调用 `rewrite_html(body)`；`html.py` 已确认调用 `rewrite_ad(text)`。因此广告处理入口真实存在并已经通过日志验证。

## 五、当前广告处理基线

当前 `mirror/mirror_v2/rewrite/ad.py` 的 `rewrite_ad()` 为：

```python
def rewrite_ad(text):
    """
    Advertisement processing is completely disabled.

    The source advertisement HTML is returned unchanged.
    """
    return text
```

当前状态：原站广告保留；广告屏蔽关闭；V2 自有广告注入关闭；单条广告实验已移除；`_block_original_ads` 已移除；`SINGLE_AD_TEST` 已移除。

`ad.py` 虽然仍有早期 pre-roll 辅助函数及 `_build_ad_html()`，但当前 `rewrite_ad()` 不调用它们。

## 六、当前 ad_config.py

`mirror/mirror_v2/config/ad_config.py` 当前：

```python
AD_ENABLED = False
```

旧配置仍有：`AD_REDIRECT_URL`、`AD_MEDIA_URL`、`AD_COUNTDOWN`、`AD_ALLOW_SKIP`、`AD_COOKIE_NAME`、`AD_COOKIE_MAX_AGE`。由于 `rewrite_ad()` 原样返回，它们当前不参与广告处理。

## 七、广告实验关键结论

曾测试底部漂浮广告：`https://65.jj10257.vip/?cid=8557280`，图片：`https://n0228.cdn.svlqgh.com/js3mg5glshit.gif`。

同一个 href 可以出现在多个位置，不同位置的 DOM 容器并不统一。曾出现 `matched=3 containers_removed=1`。这证明单纯“看到链接就删除”不能覆盖全部广告，也证明某个特殊 DOM 容器不能作为全站规则。

因此最终确定必须建立广告类型体系。

## 八、当前第一种广告类型：VIDEO CARD

首页找到适合测试的普遍类型：`video_card`。

广告链接：`https://evexymcv.cxksgtl.cc:6704/88.html?cid=4957645`

实际 DOM 已确认：

```html
<div class="video-elem mb-3">
 <a class="display d-block"
    href="https://evexymcv.cxksgtl.cc:6704/88.html?cid=4957645"
    rel="noopener nofollow"
    target="_blank">
  <div class="scale"></div>
  <div class="img" style="background-image: url('https://img.alicdn.com/imgextra/i2/O1CN01OE8est1mH4xmJAFFl_!!2221328234928-1-fleamarket.gif')"></div>
 </a>
</div>
```

目标容器：`.video-elem.mb-3`

正式逻辑应为：黑名单链接 → 类型 `video_card` → 找到匹配 href 的 `<a>` → 向上找到所属 `.video-elem.mb-3` → 删除完整容器。

## 九、最近一次 VIDEO CARD 测试

曾尝试修改旧的 `_block_single_test_ad()`，但当前 `ad.py` 已没有该函数，因此脚本输出 `ERROR: 找不到单条测试函数或 rewrite_ad`。后续实际测试仍得到：`TARGET HREF: 3`、`TARGET IMAGE: 1`、`VIDEO CARD COUNT: 4`、没有 `VIDEO_CARD_TEST` 日志。

结论：**VIDEO CARD 尚未真正屏蔽。** 当前仍是干净基线。

## 十、下一步正式实现方式

不要再使用 `_block_single_test_ad()` 作为临时函数。直接建立正式类型处理器，例如：

```python
VIDEO_CARD_AD_BLACKLIST = {
    "https://evexymcv.cxksgtl.cc:6704/88.html?cid=4957645",
}

def _remove_video_card_ads(text):
    ...

def rewrite_ad(text):
    text = _remove_video_card_ads(text)
    return text
```

第一次 VIDEO CARD 测试成功后，该处理器就保留为正式模块，而不是做完实验再推倒。

## 十一、VIDEO CARD 成功标准

1. 目标 href 从输出 HTML 消失。
2. 对应广告图片随完整容器消失。
3. 视频卡片数量按预期减少。
4. 普通视频卡片不被误删。
5. 视频真实 `data-src` 不受影响。
6. HLS URL 不受影响。
7. 其他广告类型不被误删。
8. 日志明确记录广告类型、黑名单命中数量、容器删除数量。

## 十二、后续路线

**阶段 1：VIDEO CARD**，先完成并验收。

**阶段 2：横幅**，找到首页真实横幅广告，建立 `blacklist link + banner 类型 + banner 容器`。

**阶段 3：文字广告位**，建立 `blacklist link + text/text-slot 类型 + 对应容器`。

**阶段 4：首页 + 分类页回归**。首页和分类页预计具有高度共性的广告类型；先让首页类型体系稳定，再验证分类页。

**阶段 5：播放页**。最后处理，因为播放页结构可能不同。

## 十三、当前未完成

- VIDEO CARD 正式处理器尚未完成。
- 横幅广告尚未处理。
- 文字广告位尚未处理。
- 首页广告类型尚未全部分类。
- 分类页尚未全面验证。
- 播放页尚未开始。
- 统一广告规则配置结构尚未最终确定。
- 完整误杀回归测试尚未完成。

## 十四、重要阶段备份

```text
91porny_STAGE4.5_MEDIA_CHAIN_20260901_123228.tar.gz
91porny_STAGE5.3_PLAYER_CHAIN_20260901_130510.tar.gz
91porny_STAGE5.7_MEDIA_PLAYBACK_CHAIN_20260901_135024.tar.gz
91porny_STAGE5.8_PRE_ROLL_AD_AUDIT_20260901_141758.tar.gz
91porny_STAGE5.8_PRE_ROLL_AD_FINAL_20260901_142901.tar.gz
91porny_STAGE6.5_AD_MODULE_20260901_154414.tar.gz
91porny_STAGE6_SAFE_20260901_171315.tar.gz
91porny_STAGE6.7.10_IMAGE_20260902_115640.tar.gz
91porny_STAGE6_ATTACK_SURFACE_TEST03_20260903_155852.tar.gz
91porny_STAGE6_PRE_AD_BLOCK_20260903_185000.tar.gz
```

`STAGE6.5_AD_MODULE` 和 `STAGE6_SAFE` 均包含广告相关的 `ad.py`、`ad_config.py`、`html.py`。

这些备份属于不同阶段，不能未经比较就认为某个备份等于最初版本。

## 十五、当前实验备份

```text
mirror/mirror_v2/config/ad_config.py.bak_before_ad_block_20260903_195705
mirror/mirror_v2/config/ad_config.py.bak_before_disable_ad_20260903_204337
mirror/mirror_v2/config/ad_config.py.bak_before_original_ad_block_20260903_174556
mirror/mirror_v2/rewrite/ad.py.bak_before_ad_block_20260903_195705
mirror/mirror_v2/rewrite/ad.py.bak_before_original_ad_block_20260903_174556
mirror/mirror_v2/rewrite/ad.py.bak_before_single_ad_test_20260903_210855
mirror/mirror_v2/rewrite/ad.py.bak_before_dom_single_ad_test_20260903_211252
mirror/mirror_v2/rewrite/ad.py.bak_before_ad_path_debug_20260903_211710
mirror/mirror_v2/rewrite/ad.py.bak_before_real_container_test_20260903_212734
mirror/mirror_v2/rewrite/ad.py.bak_before_disable_all_ad_processing_20260903_220232
```

这些是不同时间点的实验状态，不能混用。

## 十六、迁移到公司 Plus 账号

将本文件上传到新的公司 Plus 账号。新会话第一句话建议直接使用：

> 这是 91porny Mirror V2 项目的恢复上下文。请先完整阅读这份记录，不要重新设计项目，也不要跳过已经验证的阶段。当前广告处理已经恢复到干净基线：rewrite_ad() 原样返回 HTML，AD_ENABLED=False。下一步只做 VIDEO CARD 广告，按照“广告链接黑名单 + 广告类型 + DOM 容器”的方式逐步验收。先检查当前代码，再给出修改方案。

不要直接恢复旧广告屏蔽代码。当前真正基线就是：`rewrite_ad() → 原样返回 HTML`、`AD_ENABLED = False`。

## 十七、一句话状态

**91porny Mirror V2 的基础代理、HTML 重写入口、媒体边界和图片链路已经建立；广告处理现在处于干净基线。下一步从 VIDEO CARD 开始，以“黑名单链接 + 广告类型 + DOM 容器”的方式逐类型建立正式广告过滤系统。**
