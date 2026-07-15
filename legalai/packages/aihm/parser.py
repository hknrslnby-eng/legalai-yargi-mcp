"""HUDOC HTML → düz metin dönüşümü ve bölümlere ayırma.

Karar metinleri tipik olarak PROCEDURE / THE FACTS / THE LAW /
FOR THESE REASONS (operative) ve varsa bir ayrı görüş (DISSENTING /
SEPARATE / CONCURRING OPINION) bölümlerinden oluşur (bkz.
FORK-KAPSAMLI-PLAN.md §4.1, §4.4). Ayrı görüş başlıkları için
`legalai.packages.layers.dissent_detector` ile aynı liste kullanılır —
tutarlılık için tek bir kaynak.
"""
from __future__ import annotations

import re
from html import unescape

from legalai.packages.layers.dissent_detector import DEFAULT_DISSENT_HEADERS

_STYLE_RE = re.compile(r"<style>.*?</style>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")

SECTION_MARKERS: list[tuple[str, str]] = [
    ("procedure", "PROCEDURE"),
    ("facts", "THE FACTS"),
    ("law", "THE LAW"),
    ("operative", "FOR THESE REASONS"),
]


def html_to_text(html: str) -> str:
    """HUDOC'un `app/conversion/docx/html/body` çıktısını düz metne çevirir."""
    text = _STYLE_RE.sub("", html)
    text = _TAG_RE.sub(" ", text)
    text = unescape(text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def parse_sections(text: str) -> dict[str, str]:
    """Düz metni PROCEDURE/THE FACTS/THE LAW/FOR THESE REASONS ve (varsa)
    ayrı görüş bölümlerine ayırır. Bulunamayan bölümler sonuçta yer almaz."""
    positions: list[tuple[int, str]] = []
    for key, marker in SECTION_MARKERS:
        idx = text.find(marker)
        if idx != -1:
            positions.append((idx, key))

    separate_idx: int | None = None
    for header in DEFAULT_DISSENT_HEADERS:
        idx = text.find(header)
        if idx != -1 and (separate_idx is None or idx < separate_idx):
            separate_idx = idx
    if separate_idx is not None:
        positions.append((separate_idx, "separate"))

    positions.sort()
    sections: dict[str, str] = {}
    for i, (start, key) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        sections[key] = text[start:end].strip()
    return sections
