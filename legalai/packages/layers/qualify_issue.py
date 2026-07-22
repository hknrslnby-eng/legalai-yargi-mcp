"""QualifyIssue — soru metnindeki kelimelerden hangi yargı türüne ait
olduğunu tahmin eder.

`ctx.jurisdiction_id` çağıran taraf (örn. `jurisdiction_hint` parametresi)
tarafından zaten belirtilmişse bu katman ona dokunmaz — sadece otomatik
tespit gerektiğinde çalışır. Skor detayları `ctx.jurisdiction_scores`'a
yazılır, böylece hangi kelimelerin karar verdiği izlenebilir.
"""
from __future__ import annotations

from legalai.packages.jurisdictions.keywords import JURISDICTION_KEYWORDS
from legalai.packages.jurisdictions.selection import guess_jurisdictions
from legalai.packages.layers.related_law_selection import select_related_law_domains
from legalai.packages.layers.pipeline import Context


def guess_jurisdiction(question: str) -> tuple[str | None, dict[str, int]]:
    """Basit kelime eşleştirmesiyle en olası yargı türünü tahmin eder.
    Hiçbir kelime eşleşmezse (None, {}) döner."""
    lowered = question.lower()
    scores: dict[str, int] = {}
    for jid, keywords in JURISDICTION_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw.lower() in lowered)
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
            if not ctx.jurisdiction_ids:
                ctx.jurisdiction_ids = [ctx.jurisdiction_id]
            related = select_related_law_domains(
                question=ctx.question,
                primary_domain=ctx.jurisdiction_id,
                supporting_domains=ctx.jurisdiction_ids[1:],
                expert_lenses=ctx.expert_lenses,
            )
            ctx.expert_lenses = list(dict.fromkeys([*ctx.expert_lenses, *related.supporting]))
            ctx.trace.append({
                "layer": self.name,
                "related_law_supporting": list(related.supporting),
                "related_law_reasons": list(related.reasons),
                "related_law_excluded": list(related.excluded),
            })
            return ctx

        selection = guess_jurisdictions(ctx.question)
        ctx.jurisdiction_id = selection.primary
        ctx.jurisdiction_ids = [selection.primary, *selection.supporting]
        ctx.expert_lenses = list(dict.fromkeys([
            *selection.expert_lenses,
            *(selection.related_law.supporting if selection.related_law else ()),
        ]))
        ctx.jurisdiction_confidence = selection.confidence
        ctx.jurisdiction_scores = selection.scores
        if selection.related_law:
            ctx.trace.append({
                "layer": self.name,
                "related_law_supporting": list(selection.related_law.supporting),
                "related_law_reasons": list(selection.related_law.reasons),
                "related_law_excluded": list(selection.related_law.excluded),
            })
        return ctx
