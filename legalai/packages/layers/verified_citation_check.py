"""VerifiedCitationCheck — LLM cevabındaki her `[#doc_id]` referansının
gerçekten `ctx.documents` içinde bulunduğunu doğrular. Uydurma (halüsine
edilmiş) bir referans varsa cevabı REDDEDER ve `GroundedGenerator`'ı bir
düzeltme talimatıyla tekrar çağırır (en fazla `max_retries` kez).

Bkz. FORK-KAPSAMLI-PLAN.md Hafta 7 agent promptu ve Hafta 15'te aynı
"reddet ve tekrar dene" deseninin referans verildiği not.
"""
from __future__ import annotations

import re

from legalai.packages.layers.grounded_generator import GroundedGenerator
from legalai.packages.layers.pipeline import Context

_CITATION_RE = re.compile(r"\[#([^\]\s]+)\]")


def extract_citations(answer: str | None) -> list[str]:
    """Cevap metnindeki `[#id]` referanslarını, ilk geçiş sırasıyla ve
    tekrarsız olarak döner."""
    if not answer:
        return []
    seen: list[str] = []
    for match in _CITATION_RE.findall(answer):
        if match not in seen:
            seen.append(match)
    return seen


class VerifiedCitationCheck:
    name = "verified_citation_check"

    def __init__(self, generator: GroundedGenerator | None = None, max_retries: int = 2) -> None:
        self._generator = generator or GroundedGenerator()
        self._max_retries = max_retries

    async def run(self, ctx: Context) -> Context:
        valid_ids = {doc.id for doc in ctx.documents}
        attempts = 0

        while True:
            if ctx.answer is None:
                # LLM yapılandırılmamış/çağrı başarısız — tekrar denemek faydasız.
                ctx.citations = []
                ctx.trace.append({"layer": self.name, "attempts": attempts, "skipped": True})
                return ctx

            citations = extract_citations(ctx.answer)
            invalid = [c for c in citations if c not in valid_ids]

            if not invalid:
                ctx.citations = citations
                ctx.trace.append({"layer": self.name, "attempts": attempts, "valid": True})
                return ctx

            if attempts >= self._max_retries:
                # Son çare: uydurma referansları at, gerçek olanları raporla.
                ctx.citations = [c for c in citations if c in valid_ids]
                ctx.trace.append(
                    {
                        "layer": self.name,
                        "attempts": attempts,
                        "gave_up": True,
                        "invalid_citations": invalid,
                    }
                )
                return ctx

            attempts += 1
            ctx.trace.append(
                {"layer": self.name, "attempts": attempts, "invalid_citations": invalid}
            )
            valid_ids_repr = ", ".join(sorted(valid_ids)) or "(hiçbiri)"
            ctx.citation_retry_hint = (
                f"Önceki cevabın {invalid} kaynak kodlarını kullandı ama bunlar "
                f"verilen belgeler arasında YOK. SADECE şu belge kimliklerini "
                f"kullanarak cevabı yeniden yaz: {valid_ids_repr}."
            )
            ctx = await self._generator.run(ctx)
