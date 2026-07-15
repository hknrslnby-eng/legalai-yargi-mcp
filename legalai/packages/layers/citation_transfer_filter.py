"""CitationTransferFilter — taraf/bilirkişi aktarım cümlelerini (mahkemenin
kendi gerekçesi olmayan, sadece aktarılan iddia/savunma cümlelerini) ana
metinden ayıklar.

Bkz. FORK-KAPSAMLI-PLAN.md §3.1 (`transfer_markers`). Marker listesi Hafta
3'te jurisdiction profile'dan gelecek; şimdilik `hukuk.yaml` taslağındaki
varsayılanlar sabit kullanılıyor.
"""
from __future__ import annotations

import re

from legalai.packages.layers.pipeline import Context

DEFAULT_TRANSFER_MARKERS = [
    "ilk derece mahkemesi",
    "davacı vekili",
    "davalı",
    "bilirkişi raporunda",
    "iddia edilmiştir",
    "savunulmuştur",
]

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def filter_transfers(text: str, markers: list[str] | None = None) -> tuple[str, list[str]]:
    """Metni cümlelere böler; transfer_marker içeren cümleleri ayıklar.
    (kalan_metin, çıkarılan_cümleler) döner."""
    markers = markers or DEFAULT_TRANSFER_MARKERS
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]

    kept: list[str] = []
    transferred: list[str] = []
    for sentence in sentences:
        lowered = sentence.lower()
        if any(marker in lowered for marker in markers):
            transferred.append(sentence)
        else:
            kept.append(sentence)

    return " ".join(kept), transferred


class CitationTransferFilter:
    name = "citation_transfer_filter"

    async def run(self, ctx: Context) -> Context:
        for doc in ctx.documents:
            kept_text, _transferred = filter_transfers(doc.body)
            doc.body = kept_text
        return ctx
