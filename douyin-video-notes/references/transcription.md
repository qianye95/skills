# 抖音视频文字稿提取（音频直链 + 转写）

单条视频从打开页面到拿到完整逐字稿的完整链路。转写底层复用 `doubao-video-extract` skill，本文件只记录抖音特有的步骤与已踩的坑。

## 1. 获取音频直链（浏览器）

1. 用浏览器打开视频页 `https://www.douyin.com/video/{video_id}`（免登录可访问）。
2. 播放视频（或等待自动播放），用 `bu.network_requests()` 抓取网络请求。
3. 在请求中找 `douyinvod.com` 直链，取 **`media-audio-und-mp4a`** 类型的 URL（音频直链）。

**红线**：
- **不要用 `media-video-hvc1`**——它是纯视频流、无音轨，转写必得空 transcript（实测 46 字节空壳）。
- 同一视频可能有多个分片/清晰度直链，优先取完整的音频直链；合集分块流可能只取到几秒开头（如 4.1 秒）导致转写为空，此时换分片或标注"无口播/抓取不全"。

## 2. 下载音频（curl + 防盗链）

音频直链 CDN 有防盗链，直接下载会 403。必须：

```bash
curl -L -o audio_raw.mp4 \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Referer: https://www.douyin.com/" \
  "<media-audio-und-mp4a_url>"
```

## 3. 转纯音频 mp4（ffmpeg 封装）

下载得到的音频是 mp4 容器内的 AAC。飞书妙记统一入口只认 mp4 等视频扩展名、不认 .mp3，所以**用 ffmpeg 重封装为纯音频 mp4**：

```bash
ffmpeg -i audio_raw.mp4 -vn -c:a copy audio_only.mp4
```

（若环境无 ffmpeg，也可走 doubao-video-extract 的 PyAV 转 mp3 后按需封装；以实际可用工具为准。）

## 4. 飞书妙记转写（复用 doubao-video-extract）

```bash
cd "<doubao-video-extract skill 根目录>"
python3 scripts/minutes/social_video_to_minutes.py "/path/to/audio_only.mp4" --run-lark
```

- 命令细节、授权预检、产物读取严格遵循 `doubao-video-extract/references/lark-minutes-handoff.md`。
- **首次返回常为空壳 transcript**（只有时间戳+关键词，无正文）。等 2~5 分钟重拉：

```bash
lark-cli vc +notes --minute-tokens <minute_token> --output-dir minutes --format json --overwrite
```

直到 transcript 出现完整正文。重试次数与等待以脚本输出为准。

## 5. 转写产物

- transcript：完整逐字稿（保留时间戳）。
- chapters：章节摘要（可吸收为笔记的"章节要点"）。
- keywords：关键词（可吸收为笔记标签候选）。

## 5.5 SRT 字幕生成（标准字幕文件，可选但推荐）

每篇笔记转写完成后，用内置脚本把带时间戳的逐字稿转成标准 SRT 字幕文件（可直接导入剪映/PR/字幕工具）：

```bash
python3 "<douyin-video-notes skill 根目录>/scripts/transcript_to_srt.py" "<笔记或transcript路径>" [--total <视频总秒数>]
```

- 输入：妙记 transcript 原文（`Speaker 1 00:00:00.040 正文...` 排版），或笔记 md（自动提取 `## 完整逐字稿` 章节）。
- 输出：同目录 `<文件名>.srt`，每条字幕带起止时间（起=本段时间戳，止=下一段时间戳；最后一段按字数估算，`--total` 可传入视频总秒数约束）。
- `--check` 参数可先验证可解析段落数；无口播视频不生成 SRT（无时间轴内容）。
- SRT 文件命名与笔记一致：`NNNN_标题.srt`，与笔记同目录交付。
- 注意：SRT 文本与逐字稿同源，个别同音字错误属 ASR 固有问题，如需精确可后续人工校对。

## 6. 无口播视频处理

部分视频（训练集锦、纯音乐/格斗短片）没有口播：
- 妙记转写为空壳是**正常现象**，不代表抓取失败。
- 处理：如实标注"成功（无口播）"或"无口播训练集锦"，笔记保留真实转录内容，不编造；是否保留由用户决定。
