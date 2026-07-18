"""SelectJurisdictionProfile — `ctx.jurisdiction_id`'nin geçerli bir profile
karşılık geldiğini doğrular; QualifyIssue tahmin edemediyse veya profil
bulunamıyorsa güvenli varsayım olarak "hukuk" profiline düşer (en yaygın
yargı türü). Bkz. FORK-KAPSAMLI-PLAN.md §5.3.
"""
from __future__ import annotations

from legalai.packages.jurisdictions.loader import JurisdictionNotFoundError, load_profile
from legalai.packages.layers.pipeline import Context

DEFAULT_JURISDICTION = "diger"


class SelectJurisdictionProfile:
    name = "select_jurisdiction_profile"

    async def run(self, ctx: Context) -> Context:
        jid = ctx.jurisdiction_id or (ctx.jurisdiction_ids[0] if ctx.jurisdiction_ids else DEFAULT_JURISDICTION)
        try:
            load_profile(jid)
        except JurisdictionNotFoundError:
            jid = DEFAULT_JURISDICTION
            load_profile(jid)

        ctx.jurisdiction_id = jid
        candidates = [jid, *ctx.jurisdiction_ids]
        valid_ids: list[str] = []
        for candidate in dict.fromkeys(candidates):
            try:
                load_profile(candidate)
            except JurisdictionNotFoundError:
                continue
            valid_ids.append(candidate)
        ctx.jurisdiction_ids = valid_ids or [jid]
        return ctx
