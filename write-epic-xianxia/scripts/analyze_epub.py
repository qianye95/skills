#!/usr/bin/env python3
"""Extract aggregate Chinese prose statistics from an EPUB without retaining text."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import zipfile
from collections import Counter
from html import unescape
from pathlib import Path
from xml.etree import ElementTree


CHAPTER_RE = re.compile(r"(?:^|/)Chapter(\d+)\.xhtml$", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?；;])")
TITLE_RE = re.compile(r"<h[1-6][^>]*>(.*?)</h[1-6]>", re.IGNORECASE | re.DOTALL)
PARAGRAPH_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
HAN_RE = re.compile(r"[\u3400-\u9fff]")

MARKERS = (
    "忽然",
    "突然",
    "顿时",
    "刹那",
    "瞬间",
    "此时",
    "而后",
    "但是",
    "然而",
    "纵然",
    "仿佛",
    "犹如",
    "竟然",
    "终于",
    "直接",
    "与此同时",
)

SCALE_TERMS = (
    "浩瀚",
    "无垠",
    "苍茫",
    "枯寂",
    "震撼",
    "恐怖",
    "无尽",
    "永恒",
    "古老",
    "神秘",
    "庞大",
    "滔天",
    "绝世",
)


def clean_fragment(fragment: str) -> str:
    text = TAG_RE.sub("", fragment)
    text = unescape(text).replace("\u3000", " ")
    return SPACE_RE.sub(" ", text).strip()


def quantile(values: list[int], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 2)


def describe(values: list[int]) -> dict[str, float]:
    if not values:
        return {"mean": 0, "median": 0, "p10": 0, "p90": 0}
    return {
        "mean": round(statistics.fmean(values), 2),
        "median": round(statistics.median(values), 2),
        "p10": quantile(values, 0.10),
        "p90": quantile(values, 0.90),
    }


def parse_xhtml(raw: bytes) -> tuple[str, list[str]]:
    decoded = raw.decode("utf-8", errors="replace")
    try:
        root = ElementTree.fromstring(decoded)
        title = ""
        paragraphs: list[str] = []
        for element in root.iter():
            tag = element.tag.rsplit("}", 1)[-1].lower()
            text = clean_fragment("".join(element.itertext()))
            if tag in {"h1", "h2", "h3"} and text and not title:
                title = text
            elif tag == "p" and text:
                paragraphs.append(text)
        return title, paragraphs
    except ElementTree.ParseError:
        title_match = TITLE_RE.search(decoded)
        title = clean_fragment(title_match.group(1)) if title_match else ""
        return title, [
            text
            for match in PARAGRAPH_RE.finditer(decoded)
            if (text := clean_fragment(match.group(1)))
        ]


def count_terms(text: str, terms: tuple[str, ...]) -> dict[str, int]:
    return {term: text.count(term) for term in terms}


def normalize_rate(count: int, total_han: int) -> float:
    return round(count * 10_000 / total_han, 3) if total_han else 0.0


def analyze(epub_path: Path) -> dict[str, object]:
    chapters: list[tuple[int, str, list[str]]] = []
    parse_failures: list[str] = []
    with zipfile.ZipFile(epub_path) as archive:
        for name in archive.namelist():
            match = CHAPTER_RE.search(name)
            if not match:
                continue
            try:
                title, paragraphs = parse_xhtml(archive.read(name))
            except Exception:
                parse_failures.append(name)
                continue
            if paragraphs:
                chapters.append((int(match.group(1)), title, paragraphs))

    chapters.sort(key=lambda item: item[0])
    all_paragraphs = [paragraph for _, _, paragraphs in chapters for paragraph in paragraphs]
    all_text = "\n".join(all_paragraphs)
    han_count = len(HAN_RE.findall(all_text))
    paragraph_lengths = [len(HAN_RE.findall(paragraph)) for paragraph in all_paragraphs]
    sentences = [
        sentence.strip()
        for paragraph in all_paragraphs
        for sentence in SENTENCE_SPLIT_RE.split(paragraph)
        if HAN_RE.search(sentence)
    ]
    sentence_lengths = [len(HAN_RE.findall(sentence)) for sentence in sentences]
    title_lengths = [
        len(HAN_RE.findall(title))
        for _, title, _ in chapters
        if HAN_RE.search(title)
    ]
    punctuation = Counter(char for char in all_text if char in "，。！？；：、…—“”")
    dialogue_paragraphs = sum(
        1
        for paragraph in all_paragraphs
        if paragraph.lstrip().startswith(("“", "「", "『"))
    )

    bands: dict[str, object] = {}
    band_size = max(1, len(chapters) // 3)
    for label, subset in {
        "early": chapters[:band_size],
        "middle": chapters[band_size : 2 * band_size],
        "late": chapters[2 * band_size :],
    }.items():
        band_paragraphs = [
            paragraph for _, _, paragraphs in subset for paragraph in paragraphs
        ]
        band_text = "\n".join(band_paragraphs)
        band_han = len(HAN_RE.findall(band_text))
        band_sentences = [
            sentence.strip()
            for paragraph in band_paragraphs
            for sentence in SENTENCE_SPLIT_RE.split(paragraph)
            if HAN_RE.search(sentence)
        ]
        band_lengths = [len(HAN_RE.findall(sentence)) for sentence in band_sentences]
        bands[label] = {
            "chapters": len(subset),
            "han_characters": band_han,
            "sentence_length": describe(band_lengths),
            "exclamation_per_10k": normalize_rate(band_text.count("！"), band_han),
            "question_per_10k": normalize_rate(band_text.count("？"), band_han),
            "dialogue_paragraph_ratio": round(
                sum(
                    1
                    for paragraph in band_paragraphs
                    if paragraph.lstrip().startswith(("“", "「", "『"))
                )
                / max(1, len(band_paragraphs)),
                4,
            ),
        }

    marker_counts = count_terms(all_text, MARKERS)
    scale_counts = count_terms(all_text, SCALE_TERMS)
    return {
        "source": {
            "filename": epub_path.name,
            "chapter_files": len(chapters),
            "parse_failures": len(parse_failures),
        },
        "corpus": {
            "han_characters": han_count,
            "paragraphs": len(all_paragraphs),
            "sentences": len(sentences),
        },
        "sentence_length_han": describe(sentence_lengths),
        "paragraph_length_han": describe(paragraph_lengths),
        "chapter_title_length_han": describe(title_lengths),
        "ratios": {
            "dialogue_paragraph_ratio": round(
                dialogue_paragraphs / max(1, len(all_paragraphs)), 4
            ),
            "short_sentence_le_10_ratio": round(
                sum(length <= 10 for length in sentence_lengths)
                / max(1, len(sentence_lengths)),
                4,
            ),
            "long_sentence_ge_40_ratio": round(
                sum(length >= 40 for length in sentence_lengths)
                / max(1, len(sentence_lengths)),
                4,
            ),
        },
        "punctuation_per_10k_han": {
            mark: normalize_rate(count, han_count)
            for mark, count in punctuation.most_common()
        },
        "transition_markers_per_10k_han": {
            term: normalize_rate(count, han_count)
            for term, count in sorted(
                marker_counts.items(), key=lambda item: item[1], reverse=True
            )
        },
        "scale_lexicon_per_10k_han": {
            term: normalize_rate(count, han_count)
            for term, count in sorted(
                scale_counts.items(), key=lambda item: item[1], reverse=True
            )
        },
        "chronological_bands": bands,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze aggregate prose traits in an EPUB without exporting its text."
    )
    parser.add_argument("epub", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = analyze(args.epub)
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
