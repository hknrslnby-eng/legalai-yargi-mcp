"""ArgumentStrengthScorer — her belgenin, üretilecek cevaba temel
alınacak argüman gücünü tahmini olarak puanlar. Bkz.
FORK-KAPSAMLI-PLAN.md §5.3.

Üç bileşen kullanılır:
1. **Hiyerarşi konumu** — jurisdiction profile'ın `hierarchy` listesindeki
   (yüksek→düşük) konum; İBK/HGK gibi üst organların kararı, ilk derece
   kararından daha güçlü kabul edilir.
2. **Ratio uzunluğu** — `RatioDictumFilter`'ın ayırdığı ratio metni ne
   kadar uzun/somutsa gerekçe o kadar güçlü sayılır (basit ama tekrarlanabilir
   bir vekil ölçüt; gerçek bir "gerekçe kalitesi" modeli değildir).
3. **Karşı oy cezası** — `DissentDetector` bir karşı oy bulduysa, kararın
   tartışmalı olduğunu gösterir; skor hafifçe düşürülür.

Not: `hierarchy` eşleştirmesi, alıntı (citation) metninde tam sözcük arar
(örn. "DAIRE" → "... Dairesi ..."). Bu bir sezgiseldir; kesin değildir.
"""
from __future__ import annotations

from legalai.packages.jurisdictions.loader import JurisdictionNotFoundError, load_profile
from legalai.packages.layers.pipeline import Context

_MAX_RATIO_LEN_FOR_FULL_SCORE = 500
_DISSENT_PENALTY = 0.15


def _tr_lower(text: str) -> str:
    """Türkçe büyük 'İ' harfini `str.lower()` ile küçültünce Python, ASCII
    'i' değil 'i' + birleşen nokta (U+0307) üretir — bu da alt dize
    eşleşmesini bozar (örn. "İBK".lower() "IBK".lower()'a eşit olmaz).
    Bu yardımcı, birleşen noktayı at, karşılaştırma tutarlı olsun."""
    return text.lower().replace("\u0307", "")


def hierarchy_weight(citation: str, hierarchy: list[str]) -> float:
    """`hierarchy` yüksekten alçağa sıralıdır; en yüksek eşleşen seviyeye
    göre 1.0 (en üst) ile 0.2 (eşleşme yok) arası bir ağırlık döner."""
    if not hierarchy:
        return 0.5
    lowered = _tr_lower(citation)
    for idx, level in enumerate(hierarchy):
        needle = _tr_lower(level.replace("_", " "))
        if needle and needle in lowered:
            return round(1.0 - (idx / len(hierarchy)) * 0.8, 3)
    return 0.2


def ratio_length_weight(ratio_text: str) -> float:
    return round(min(len(ratio_text) / _MAX_RATIO_LEN_FOR_FULL_SCORE, 1.0), 3)


class ArgumentStrengthScorer:
    name = "argument_strength_scorer"

    async def run(self, ctx: Context) -> Context:
        hierarchy: list[str] = []
        if ctx.jurisdiction_id:
            try:
                hierarchy = load_profile(ctx.jurisdiction_id).hierarchy
            except JurisdictionNotFoundError:
                hierarchy = []

        ratio_by_doc = {r["doc_id"]: r["text"] for r in ctx.ratios}
        dissent_doc_ids = {d["doc_id"] for d in ctx.dissents}

        scores = []
        for doc in ctx.documents:
            h_score = hierarchy_weight(doc.citation, hierarchy)
            r_score = ratio_length_weight(ratio_by_doc.get(doc.id, ""))
            penalty = _DISSENT_PENALTY if doc.id in dissent_doc_ids else 0.0
            strength = max(0.0, round(h_score * 0.5 + r_score * 0.5 - penalty, 3))
            scores.append({"doc_id": doc.id, "strength": strength})

        ctx.argument_scores = scores
        return ctx
