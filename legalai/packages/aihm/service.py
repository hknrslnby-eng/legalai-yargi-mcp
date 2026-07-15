"""AİHM üst düzey fonksiyonları — MCP tool'larının çağırdığı asıl mantık.
Bkz. FORK-KAPSAMLI-PLAN.md §4.2."""
from __future__ import annotations

from datetime import date as date_cls
from typing import Any

from legalai.packages.aihm.cache import get_cached, set_cached
from legalai.packages.aihm.client import HudocClient
from legalai.packages.aihm.parser import parse_sections
from legalai.packages.aihm.types import AIHMDecision

_client: HudocClient | None = None


def _get_client() -> HudocClient:
    global _client
    if _client is None:
        _client = HudocClient()
    return _client


def _parse_date(value: str | None) -> date_cls | None:
    if not value:
        return None
    try:
        return date_cls.fromisoformat(value[:10])
    except ValueError:
        return None


def _parse_articles(raw: str | None) -> list[str]:
    return [a for a in (raw or "").split(";") if a]


def _parse_importance(raw: str | None) -> int | None:
    if raw and raw.isdigit():
        return int(raw)
    return None


async def aihm_karar_ara(
    query: str = "",
    respondent: str = "TUR",
    article: str | None = None,
    importance: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """HUDOC'ta karar arar; her sonuç için özet metadata döner.
    Bkz. FORK-KAPSAMLI-PLAN.md §4.2."""
    client = _get_client()
    columns_list = await client.search(
        query=query,
        respondent=respondent,
        article=article,
        importance=importance,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return [
        {
            "itemid": c.get("itemid", ""),
            "application_no": c.get("appno", ""),
            "docname": c.get("docname", ""),
            "date": (c.get("kpdate") or "")[:10],
            "articles": _parse_articles(c.get("article")),
            "respondent": c.get("respondent", ""),
            "importance": _parse_importance(c.get("importance")),
            "language": c.get("languageisocode", ""),
            "chamber": c.get("documentcollectionid", ""),
        }
        for c in columns_list
    ]


async def aihm_karar_getir(application_no: str, lang: str = "en") -> dict[str, Any]:
    """Bir başvuru numarasına karşılık gelen kararın tam metnini,
    bölümlere ayrılmış olarak getirir. TR çevirisi yoktur; istenen dilde
    bulunamazsa EN, sonra FR, sonra bulunan ilk dil döner (bkz. §4.1)."""
    lang_code = "ENG" if lang.lower() == "en" else "FRE"
    cache_key = f"appno:{application_no}:{lang_code}"

    cached = await get_cached(cache_key)
    if cached is not None:
        return cached

    client = _get_client()
    results = await client.search(respondent=None, appno=application_no, limit=5)
    if not results:
        raise ValueError(f"AİHM kararı bulunamadı: {application_no}")

    preferred = next((r for r in results if r.get("languageisocode") == lang_code), None)
    if preferred is None:
        preferred = next((r for r in results if r.get("languageisocode") == "ENG"), None)
    if preferred is None:
        preferred = next((r for r in results if r.get("languageisocode") == "FRE"), None)
    if preferred is None:
        preferred = results[0]

    itemid = preferred["itemid"]
    text = await client.get_document_text(itemid)
    sections = parse_sections(text)

    decision = AIHMDecision(
        application_no=application_no,
        respondent=preferred.get("respondent", ""),
        date=_parse_date(preferred.get("kpdate")),
        articles=_parse_articles(preferred.get("article")),
        importance=_parse_importance(preferred.get("importance")),
        chamber=preferred.get("documentcollectionid", ""),
        languages_available=[preferred.get("languageisocode", "")],
        sections=sections,
        itemid=itemid,
        docname=preferred.get("docname", ""),
    )

    payload = {
        "application_no": decision.application_no,
        "respondent": decision.respondent,
        "date": decision.date.isoformat() if decision.date else None,
        "articles": decision.articles,
        "importance": decision.importance,
        "chamber": decision.chamber,
        "languages_available": decision.languages_available,
        "sections": decision.sections,
        "itemid": decision.itemid,
        "docname": decision.docname,
    }
    await set_cached(cache_key, payload)
    return payload
