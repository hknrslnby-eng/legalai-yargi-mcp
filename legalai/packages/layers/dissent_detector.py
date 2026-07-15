"""DissentDetector — karşı oy / muhalefet şerhi bölümlerini ayırır.

Bkz. FORK-KAPSAMLI-PLAN.md §9.2. Marker listesi Hafta 3'te jurisdiction
profile'lardaki `dissent_headers` alanından okunacak; şimdilik yaygın
Türkçe ve AİHM başlıkları sabit kullanılıyor.
"""
from __future__ import annotations

import re

from legalai.packages.layers.pipeline import Context

DEFAULT_DISSENT_HEADERS = [
    "KARŞI OY",
    "MUHALEFET ŞERHİ",
    "DISSENTING OPINION",
    "CONCURRING OPINION",
    "SEPARATE OPINION",
]


def find_dissent(text: str, headers: list[str] | None = None) -> str | None:
    """Metinde bilinen bir karşı oy/muhalefet başlığı ararsa, başlıktan
    itibaren metnin kalanını döner. Bulunamazsa None döner."""
    headers = headers or DEFAULT_DISSENT_HEADERS
    pattern = re.compile("|".join(re.escape(h) for h in headers), re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return None
    return text[match.start():].strip()


class DissentDetector:
    name = "dissent_detector"

    async def run(self, ctx: Context) -> Context:
        for doc in ctx.documents:
            dissent_text = find_dissent(doc.body)
            if dissent_text:
                ctx.dissents.append({"doc_id": doc.id, "text": dissent_text, "type": "karşı_oy"})
        return ctx
