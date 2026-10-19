---
name: douyin-video-notes
description: 抖音视频文字稿提取与知识笔记生成。当用户提供抖音账号名称/账号主页链接（需批量提取该账号作品文字稿并整理成笔记）或具体抖音视频链接（需提取该视频文字稿），要求输出 Markdown 笔记文档时使用。笔记必须包含 up 主名称、发布内容标题、知识领域等标签；同时支持生成 SRT 字幕文件与采集互动指标（播放/点赞/评论/收藏/转发）用于账号对标。触发场景：抖音视频转写、提取逐字稿/文字稿、视频内容整理成笔记、批量整理某博主的视频、视频内容分析存档、生成字幕文件、博主互动数据分析。
---

# 抖音视频文字稿提取与笔记生成

把抖音视频（单个链接或整个账号的作品）转成带结构化标签的 Markdown 知识笔记：提取完整逐字稿 + 内容要点，并标注 up 主名称、发布标题、知识领域等标签。

## 输入识别

| 用户输入 | 类型 | 处理路径 |
| --- | --- | --- |
| `https://www.douyin.com/video/{video_id}` | 单视频 | 单视频流程 → 1 篇 md |
| `https://www.douyin.com/user/{sec_user_id}` 或账号名 | 账号批量 | 批量流程 → N 篇 md + 索引表 |
| 分享口令/短链 | 先解析为可访问链接 | 同上 |

账号名输入时：先经浏览器搜索或在对话中确认该账号的 sec_user_id（主页 URL 中的 `MS4wLjABAAAA...` 串），批量采集前必须锁定它。

## 执行前必读（强约束）

1. **转写底层复用 `doubao-video-extract` skill**（其 SKILL.md 及 `references/lark-minutes-handoff.md`、`references/website_extract.md`）：音频直链下载、音频转纯音频 mp4、飞书妙记上传与重拉逐字稿，全部走该 skill 的统一入口 `python3 scripts/minutes/social_video_to_minutes.py <本地mp4> --run-lark`，不另造转写通道。
2. **抖音页面操作使用 `browser-use-automation-mac` skill**（`mac_computer_use_tool`，plane=`bu`）：列表采集、视频页网络请求抓直链、作者归属验证均经浏览器完成。
3. 每次执行前重读上述两个 skill 的 SKILL.md（本 skill 不复制它们的命令细节）。

## 单视频流程

1. 浏览器打开视频页（免登录可访问）。
2. 从页面网络请求中抓取 `douyinvod.com` 的 **`media-audio-und-mp4a`** 音频直链（详见 `references/transcription.md`）。
3. curl 带 UA + Referer 下载音频 → ffmpeg 封装为纯音频 mp4。
4. 走 doubao-video-extract 的 `--run-lark` 转写；首次返回空壳 transcript 时等 2~5 分钟重拉。
5. 按 `references/note-template.md` 生成 md 笔记（含 up 主、标题、知识领域标签、完整逐字稿）。
6. **生成 SRT 字幕**：`python3 <skill根目录>/scripts/transcript_to_srt.py "<笔记md>" [--total <秒>]`，得到同名 `.srt`（无口播视频跳过）。
7. 交付：笔记文件 + SRT + 转写来源说明。

## 账号批量流程

1. **锁定账号**：确认 sec_user_id（主页 URL）；作品数、发布时间范围等先读主页"作品"tab。
2. **采集视频清单**：主页作品列表滚动加载采集（read_all 单轮上限 200 条，超长列表会截断最老视频）；早期内容走**合集通道**（`https://www.douyin.com/collection/{collection_id}/1`，逐个合集读列表）。细节与死路见 `references/douyin-collection.md`。
3. **作者归属验证 + 互动指标采集（必须验证、推荐采指标）**：合集页和列表会混入其他作者的推荐位视频。对每条候选视频打开视频页，取 `a[href*='/user/']` 的 sec_user_id，与目标账号前缀比对；非目标账号的**剔除**（移入"杂质剔除"目录并记清单），共创/他号发布单列待用户裁决。同一轮顺便采集播放量/点赞/评论/收藏/转发（方法见 `references/douyin-collection.md` §6）。
4. **逐条转写**：同单视频流程 2~4 步，可并行分片（每条独立）。
5. **生成笔记 + SRT + 索引表**：每篇按模板生成并同步 SRT；汇总 `索引总表.csv`（序号/video_id/标题/链接/来源合集/播放量/点赞/评论/收藏/转发/时长/发布时间/核心主题/状态/失败原因/笔记路径）。
6. **生成指标表（可选）**：按点赞降序生成 `指标表.csv`（标题/发布时间/四项互动），供账号对标与选题研究。
7. **交付**：笔记目录（含 SRT）+ 索引总表 + 指标表 + 杂质/失败明细清单。

## md 笔记模板与标签规则

模板、标签（知识领域等）命名与判定规则见 `references/note-template.md`。核心要求：

- **up 主名称**：取自视频页作者（批量场景须与目标账号一致，共创标注"共创"）。
- **发布内容标题**：视频标题原文。
- **知识领域标签**：按内容主题判定（营养/健身/减脂/睡眠/补剂/拳击训练/肠道健康等，可多标签），写入笔记标签区。
- **完整逐字稿**：必须原文粘贴妙记 transcript（保留时间戳），禁止缩写、改写或编造；无口播视频如实标注"无口播"。

## 平台边界与红线（踩坑实录）

- 抖音视频页免登录可访问；但主页列表未登录仅能加载约 200 条，更早作品需合集通道，仍有平台加载上限，无法穷尽时如实报告。
- **只取 `media-audio-und-mp4a`**；`media-video-hvc1` 是纯视频流无音轨，转写必得空 transcript。
- 音频直链 CDN 防盗链：curl 必须带 `User-Agent` 和 `Referer: https://www.douyin.com/`，否则 403。
- 妙记 `--run-lark` 首次返回常为空壳（仅时间戳+关键词），需等 2~5 分钟用 lark-cli `vc +notes` 重拉。
- 转写内容只能来自妙记产物，禁止用浏览器页面字幕/页面文字代替。
