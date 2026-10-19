#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把带时间戳的逐字稿转换为标准 SRT 字幕文件。

输入：
  - 妙记 transcript 原文文本（每段一行时间戳 + 后续文本行）：
        Speaker 1 00:00:00.040
        哈喽，大家好，今天想聊减脂...
        Speaker 1 00:00:37.140
        我这么操作...
  - 或一篇笔记 md（自动提取 "## 完整逐字稿" 章节）

输出：标准 SRT（序号 + 起止时间 + 文本），每条字幕起止时间取自时间戳，
结束时间 = 下一条开始时间；最后一条按 --last-duration 或按字数估算补齐。

用法：
  python3 transcript_to_srt.py <transcript.txt|note.md> [-o out.srt] [--last-duration 3]
  python3 transcript_to_srt.py --check <file>   # 只检查可解析段落数
"""
import argparse
import re
import sys

TS_RE = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})[.,](\d{1,3})")
BLOCK_RE = re.compile(r"(?:Speaker\s+\d+\s+)?(\d{1,2}:\d{2}:\d{2}[.,]\d{1,3})")

CHARS_PER_SEC = 4.5  # 中文口播约 4.5 字/秒，用于最后一段时长估算


def parse_timestamp(m):
    h, mnt, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
    ms = int(ms) * (1000 // (10 ** len(ms))) if len(ms) < 3 else int(ms)
    return h * 3600 + mnt * 60 + s + ms / 1000.0


def parse_ts_str(ts_str):
    m = TS_RE.search(ts_str)
    if not m:
        raise ValueError(f"无法解析时间戳: {ts_str}")
    return parse_timestamp(m)


def fmt_srt_time(t):
    h = int(t // 3600)
    mnt = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms >= 1000:
        ms = 0
        s += 1
    return f"{h:02d}:{mnt:02d}:{s:02d},{ms:03d}"


def extract_transcript(text):
    """从原文提取 [(start_sec, end_sec, text), ...]。

    支持两种排版：
      A) 时间戳单独一行，文本随后（妙记 transcript / 笔记逐字稿）
      B) 时间戳与文本同一行（"00:00:01 哈喽"）
    """
    lines = text.splitlines()
    blocks = []
    cur_ts = None
    cur_text = []

    def flush():
        nonlocal cur_ts, cur_text
        if cur_ts is not None and cur_text:
            blocks.append((cur_ts, None, "\n".join(cur_text).strip()))
        cur_ts = None
        cur_text = []

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        # 跳过非内容行（章节头等）
        m = BLOCK_RE.search(line)
        if m and m.start() == 0:
            flush()
            cur_ts = parse_ts_str(m.group(1))
            rest = line[m.end():].strip()
            if rest and not rest.startswith("Speaker"):
                cur_text.append(rest)
        else:
            if cur_ts is not None:
                cur_text.append(line)
    flush()

    # 组装结束时间
    for i, (start, _end, txt) in enumerate(blocks):
        if i + 1 < len(blocks):
            blocks[i] = (start, blocks[i + 1][0], txt)
    return blocks


def read_input(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    # 若输入是笔记 md，只取完整逐字稿章节
    if path.lower().endswith(".md") or "## 完整逐字稿" in content:
        m = re.search(r"##\s*完整逐字稿\s*\n(.*?)(?:\n---|\Z)", content, re.S)
        if m:
            content = m.group(1)
    return content


def build_srt(blocks, last_duration=None, total_sec=None):
    if not blocks:
        return ""
    out = []
    for i, (start, end, txt) in enumerate(blocks, 1):
        if end is None:
            est = max(3.0, len(txt) / CHARS_PER_SEC)
            if total_sec is not None and start + est > total_sec:
                est = max(0.5, total_sec - start)
            end = start + (last_duration if last_duration else est)
        clean = re.sub(r"\s+", " ", txt).strip()
        out.append(f"{i}\n{fmt_srt_time(start)} --> {fmt_srt_time(end)}\n{clean}\n")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="逐字稿 → SRT")
    ap.add_argument("input", help="逐字稿 txt 或笔记 md 路径")
    ap.add_argument("-o", "--output", help="输出 SRT 路径（默认 <输入名>.srt）")
    ap.add_argument("--last-duration", type=float, default=None, help="最后一段时长（秒），默认按字数估算")
    ap.add_argument("--total", type=float, default=None, help="视频总时长（秒），用于约束最后一段")
    ap.add_argument("--check", action="store_true", help="只统计可解析段落数")
    args = ap.parse_args()

    content = read_input(args.input)
    blocks = extract_transcript(content)

    if args.check:
        print(f"解析段落数: {len(blocks)}")
        for i, (s, e, t) in enumerate(blocks[:3], 1):
            print(f"  [{i}] {fmt_srt_time(s)} -> {fmt_srt_time(e) if e else '?'} | {t[:30]}")
        sys.exit(0 if blocks else 1)

    if not blocks:
        print("错误: 未解析到任何带时间戳的段落", file=sys.stderr)
        sys.exit(1)

    srt = build_srt(blocks, args.last_duration, args.total)
    out = args.output or (args.input.rsplit(".", 1)[0] + ".srt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(srt)
    print(f"已生成 {out}（{len(blocks)} 条字幕）")


if __name__ == "__main__":
    main()
