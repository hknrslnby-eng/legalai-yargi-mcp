"""Contextual selection of supporting legal domains.

The selector is deliberately conservative: NIS and cyber lenses are useful
for a genuine data/security issue, while criminal and administrative angles
require concrete facts rather than stereotypes or automatic liability claims.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence


@dataclass(frozen=True)
class RelatedLawSelection:
    primary: str
    supporting: tuple[str, ...]
    reasons: tuple[str, ...]
    excluded: tuple[str, ...]


def _normalize(value: str) -> str:
    return (
        value.casefold()
        .replace("ı", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
        .replace("-", "_")
    )


def _has(text: str, *terms: str) -> bool:
    return any(term in text for term in terms)


def select_related_law_domains(
    *,
    question: str,
    primary_domain: str,
    supporting_domains: Sequence[str] = (),
    expert_lenses: Sequence[str] = (),
) -> RelatedLawSelection:
    text = _normalize(question)
    context_values = {_normalize(item) for item in (primary_domain, *supporting_domains, *expert_lenses)}
    kvkk_context = bool(context_values & {"kvkk", "nis", "nis_1", "nis_2", "siber", "siber_guvenlik", "bilisim"}) or _has(
        text, "kisisel veri", "veri ihlali", "veri sizintisi", "siber saldiri", "cyber", "nis-1", "nis-2"
    )
    selected: list[str] = []
    reasons: list[str] = []

    def add(domain: str, reason: str) -> None:
        if domain not in selected and _normalize(domain) != _normalize(primary_domain):
            selected.append(domain)
            reasons.append(f"{domain}: {reason}")

    if kvkk_context:
        add("nis_1", "veri ve ağ güvenliği olayı için AB NIS-1 karşılaştırma lensi")
        add("nis_2", "kritik/önemli kuruluş ve olay bildirim yapısı için AB NIS-2 karşılaştırma lensi")
        add("siber_guvenlik", "teknik güvenlik tedbirleri, olay müdahalesi ve log/erişim akışı")

        if _has(text, "kurul", "idari", "yaptirim", "kamu", "denetim", "bildirim", "otorite"):
            add("idare", "Kurul, idari yaptırım veya kamu otoritesi bağlantısı")
        if _has(text, "suc", "fail", "saldiri", "yetkisiz erisim", "hirsizlik", "dolandir", "fidye", "kripto", "exfiltration", "insider"):
            add("ceza", "Yetkisiz erişim, saldırı veya suç isnadı ihtimalinin somut olgularla incelenmesi")
        if _has(text, "tedarikci", "vendor", "hizmet saglayici", "alt isveren", "sozlesme", "contract", "dpa"):
            add("sozlesmeler", "Veri işleme, tedarikçi veya hizmet sözleşmesi bağlantısı")
        if _has(text, "calisan", "isci", "personel", "employee", "insider", "mesai"):
            add("is_hukuku", "Çalışan erişimi, iş akışı ve işveren denetimi bağlantısı")
        if _has(text, "zarar", "tazminat", "maddi kayip", "manevi"):
            add("tazminat", "Zarar ve giderim iddiasının ayrıca incelenmesi")

    known_related = ("kvkk", "nis_1", "nis_2", "siber_guvenlik", "idare", "ceza", "sozlesmeler", "is_hukuku", "tazminat")
    excluded = tuple(domain for domain in known_related if domain not in selected and _normalize(domain) != _normalize(primary_domain))
    if not kvkk_context:
        excluded = tuple(dict.fromkeys(("kvkk", "nis_1", "nis_2", "siber_guvenlik", *excluded)))
    return RelatedLawSelection(primary_domain, tuple(selected), tuple(reasons), excluded)
