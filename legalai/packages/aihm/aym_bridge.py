"""AYM (Anayasa Mahkemesi) bireysel başvuru ↔ AİHM (HUDOC) köprüsü.

Bkz. FORK-KAPSAMLI-PLAN.md §4.5 — Hafta 5. Aynı olayda hem AYM bireysel
başvurusu hem de AİHM'e paralel bir başvuru yapılmış olabilir. Strateji:

1. AYM kararının başlığından (örn. "HASAN DURMUŞ Başvurusuna İlişkin Karar")
   başvurucu adını çıkar.
2. HUDOC'ta `respondent=TUR` + karar tarihinin ±yıl penceresi + başvurucu
   adıyla ara.
3. Aday sonuçları, `docname` alanıyla başvurucu adı arasındaki `rapidfuzz`
   benzerlik skoruna göre sırala; kullanıcıya "muhtemel eşleşme" olarak sun
   (otomatik kesin eşleştirme YAPILMAZ — kullanıcı onayı gerekir).
"""
from __future__ import annotations

import re
from typing import Any

from rapidfuzz import fuzz

from anayasa_mcp_module.bireysel_client import AnayasaBireyselBasvuruApiClient
from anayasa_mcp_module.models import AnayasaBireyselReportSearchRequest
from legalai.packages.aihm.client import HudocClient

_TITLE_NAME_RE = re.compile(
    r"^(?P<name>.+?)\s+Başvurusuna İlişkin Karar$", re.IGNORECASE
)

MIN_MATCH_SCORE = 55.0


def extract_applicant_name(title: str) -> str | None:
    """AYM karar başlığından başvurucu adını çıkarır.

    Örn: "HASAN DURMUŞ Başvurusuna İlişkin Karar" -> "HASAN DURMUŞ"
    Kalıp eşleşmezse (örn. "X ve diğerleri" veya kurumsal başvurucu gibi
    daha karmaşık başlıklar) None döner — çağıran taraf bunu kullanıcıya
    bildirmelidir.
    """
    match = _TITLE_NAME_RE.match(title.strip())
    if not match:
        return None
    return match.group("name").strip()


def extract_decision_year(decision_date_summary: str) -> int | None:
    """`DD/MM/YYYY` formatındaki AYM karar tarihinden yılı çıkarır."""
    parts = decision_date_summary.strip().split("/")
    if len(parts) != 3:
        return None
    try:
        return int(parts[2])
    except ValueError:
        return None


async def find_aym_decision(basvuru_no: str) -> dict[str, Any] | None:
    """Bir AYM bireysel başvuru numarasına karşılık gelen karar özetini bulur."""
    client = AnayasaBireyselBasvuruApiClient()
    try:
        result = await client.search_bireysel_basvuru_report(
            AnayasaBireyselReportSearchRequest(keywords=[basvuru_no], results_per_page=10)
        )
    finally:
        await client.close_client_session()

    for decision in result.decisions:
        if decision.decision_reference_no == basvuru_no:
            return {
                "title": decision.title,
                "decision_reference_no": decision.decision_reference_no,
                "decision_date_summary": decision.decision_date_summary,
                "decision_making_body": decision.decision_making_body,
            }
    return None


async def aihm_aym_kopru(aym_basvuru_no: str) -> dict[str, Any]:
    """Bir AYM bireysel başvuru numarası için muhtemel paralel AİHM
    başvurularını arar. Kesin eşleştirme yapmaz; aday listesi döner."""
    aym_decision = await find_aym_decision(aym_basvuru_no)
    if aym_decision is None:
        return {
            "aym_basvuru_no": aym_basvuru_no,
            "found": False,
            "reason": "Bu başvuru numarasıyla eşleşen bir AYM bireysel başvuru kararı bulunamadı.",
            "candidates": [],
        }

    applicant_name = extract_applicant_name(aym_decision["title"])
    if applicant_name is None:
        return {
            "aym_basvuru_no": aym_basvuru_no,
            "found": True,
            "aym_decision": aym_decision,
            "reason": (
                "AYM karar başlığından başvurucu adı otomatik çıkarılamadı "
                "(başlık kalıbı desteklenmiyor); manuel arama gerekir."
            ),
            "candidates": [],
        }

    year = extract_decision_year(aym_decision["decision_date_summary"])
    date_from = f"{year - 1}-01-01" if year else None
    date_to = f"{year + 3}-12-31" if year else None

    async with HudocClient() as hudoc:
        results = await hudoc.search(
            query=applicant_name,
            respondent="TUR",
            date_from=date_from,
            date_to=date_to,
            limit=20,
        )

    candidates = []
    for item in results:
        docname = item.get("docname", "")
        score = fuzz.partial_ratio(applicant_name.lower(), docname.lower())
        if score >= MIN_MATCH_SCORE:
            candidates.append(
                {
                    "application_no": item.get("appno", ""),
                    "docname": docname,
                    "date": (item.get("kpdate") or "").split("T")[0],
                    "match_score": round(score, 1),
                }
            )
    candidates.sort(key=lambda c: c["match_score"], reverse=True)

    return {
        "aym_basvuru_no": aym_basvuru_no,
        "found": True,
        "aym_decision": aym_decision,
        "applicant_name_used_for_search": applicant_name,
        "candidates": candidates,
        "note": (
            "Bu bir olası eşleşme listesidir, otomatik doğrulama değildir. "
            "Kullanıcı her adayın gerçek metnini (aihm_karar_getir) inceleyip "
            "onaylamalıdır."
        ),
    }
