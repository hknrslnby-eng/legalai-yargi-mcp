"""QualifyIssue — soru metnindeki kelimelerden hangi yargı türüne ait
olduğunu tahmin eder.

`ctx.jurisdiction_id` çağıran taraf (örn. `jurisdiction_hint` parametresi)
tarafından zaten belirtilmişse bu katman ona dokunmaz — sadece otomatik
tespit gerektiğinde çalışır. Skor detayları `ctx.jurisdiction_scores`'a
yazılır, böylece hangi kelimelerin karar verdiği izlenebilir.
"""
from __future__ import annotations

from legalai.packages.jurisdictions.keywords import JURISDICTION_KEYWORDS
from legalai.packages.layers.pipeline import Context


def guess_jurisdiction(question: str) -> tuple[str | None, dict[str, int]]:
    """Basit kelime eşleştirmesiyle en olası yargı türünü tahmin eder.
    Hiçbir kelime eşleşmezse (None, {}) döner."""
    lowered = question.lower()
    scores: dict[str, int] = {}
    for jid, keywords in JURISDICTION_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in lowered)
        if hits:
            scores[jid] = hits

    if not scores:
        return None, scores

    best = max(scores, key=lambda k: scores[k])
    return best, scores


class QualifyIssue:
    name = "qualify_issue"

    async def run(self, ctx: Context) -> Context:
        if ctx.jurisdiction_id:
            return ctx

        guess, scores = guess_jurisdiction(ctx.question)
        ctx.jurisdiction_id = guess
        ctx.jurisdiction_scores = scores
        return ctx
