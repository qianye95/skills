#!/usr/bin/env python3
"""Flag long exact overlaps between a candidate text and an EPUB corpus."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from html import unescape
from pathlib import Path


CHAPTER_RE = re.compile(r"(?:^|/)Chapter\d+\.xhtml$", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    text = unescape(TAG_RE.sub("", text))
    return SPACE_RE.sub("", text)


def load_epub_text(path: Path) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if CHAPTER_RE.search(name):
                chunks.append(archive.read(name).decode("utf-8", errors="replace"))
    return normalize("\n".join(chunks))


def expand_match(candidate: str, source: str, candidate_start: int, source_start: int, size: int) -> tuple[int, int]:
    left = 0
    while (
        candidate_start - left - 1 >= 0
        and source_start - left - 1 >= 0
        and candidate[candidate_start - left - 1] == source[source_start - left - 1]
    ):
        left += 1
    right = size
    while (
        candidate_start + right < len(candidate)
        and source_start + right < len(source)
        and candidate[candidate_start + right] == source[source_start + right]
    ):
        right += 1
    return candidate_start - left, candidate_start + right


def find_overlaps(candidate: str, source: str, window: int, step: int) -> list[tuple[int, int]]:
    matches: list[tuple[int, int]] = []
    for start in range(0, max(0, len(candidate) - window + 1), step):
        source_start = source.find(candidate[start : start + window])
        if source_start < 0:
            continue
        matches.append(expand_match(candidate, source, start, source_start, window))
    merged: list[tuple[int, int]] = []
    for start, end in sorted(set(matches)):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect long exact overlaps with an EPUB source."
    )
    parser.add_argument("epub", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--window", type=int, default=24)
    parser.add_argument("--step", type=int, default=6)
    args = parser.parse_args()
    if args.window < 12 or args.step < 1:
        parser.error("--window must be >= 12 and --step must be >= 1")
    source = load_epub_text(args.epub)
    candidate = normalize(args.candidate.read_text(encoding="utf-8"))
    matches = find_overlaps(candidate, source, args.window, args.step)
    result = {
        "candidate_characters": len(candidate),
        "window": args.window,
        "overlap_count": len(matches),
        "maximum_overlap_characters": max(
            (end - start for start, end in matches), default=0
        ),
        "overlaps": [
            {
                "candidate_start": start,
                "length": end - start,
                "candidate_excerpt": candidate[start : min(end, start + 40)],
            }
            for start, end in sorted(
                matches, key=lambda pair: pair[1] - pair[0], reverse=True
            )[:20]
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
