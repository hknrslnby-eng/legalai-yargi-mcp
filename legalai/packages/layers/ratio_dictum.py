"""RatioDictumFilter — bir kararın ratio decidendi (bağlayıcı gerekçe) ile
dictum (yan söz) kısımlarını ayırır.

Not: Hafta 3'te jurisdiction profile loader hazır olduğunda, marker
listeleri `configs/jurisdictions/*.yaml` dosyalarından okunacak (bkz.
FORK-KAPSAMLI-PLAN.md §3.1). Bu Hafta 2 iskeletinde `hukuk.yaml`
taslağındaki varsayılan Türkçe marker'lar sabit kullanılıyor.
"""
from __future__ import annotations

import re

from legalai.packages.layers.pipeline import Context

DEFAULT_RATIO_MARKERS = [
    "sonuç olarak",
    "kabul edildiğine göre",
    "yerleşik içtihat",
    "dairemizce",
]
DEFAULT_DICTUM_MARKERS = [
    "belirtmek gerekirse",
    "hemen ifade edelim ki",
]

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def split_ratio_dictum(
    text: str,
    ratio_markers: list[str] | None = None,
    dictum_markers: list[str] | None = None,
) -> tuple[str, str]:
    """Metni cümlelere böler; dictum marker'ı içeren cümleleri dictum'a,
    kalanları (marker'lı ya da marker'sız) ratio'ya toplar. Temkinli
    varsayım: bilinmeyen/markersiz cümle atılmaz, ratio'da kalır."""
    ratio_markers = ratio_markers or DEFAULT_RATIO_MARKERS
    dictum_markers = dictum_markers or DEFAULT_DICTUM_MARKERS

    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    if not sentences:
        return "", ""

    ratio_sentences: list[str] = []
    dictum_sentences: list[str] = []
    for sentence in sentences:
        lowered = sentence.lower()
        if any(marker in lowered for marker in dictum_markers):
            dictum_sentences.append(sentence)
        else:
            ratio_sentences.append(sentence)

    return " ".join(ratio_sentences), " ".join(dictum_sentences)


class RatioDictumFilter:
    name = "ratio_dictum"

    async def run(self, ctx: Context) -> Context:
        for doc in ctx.documents:
            ratio, dictum = split_ratio_dictum(doc.body)
            ctx.ratios.append({"doc_id": doc.id, "text": ratio})
            ctx.dictums.append({"doc_id": doc.id, "text": dictum})
        return ctx
