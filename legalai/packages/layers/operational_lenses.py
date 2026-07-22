"""Reviewable technical, commercial, cyber, financial and behavioural lenses."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from typing import Any, Literal


EvidenceStatus = Literal["user_statement", "document_backed", "hypothesis", "verification_required"]


@dataclass(frozen=True)
class OperationalFinding:
    domain: str
    label: str
    statement: str
    evidence_status: EvidenceStatus
    legal_impacts: tuple[str, ...]
    confidence: str


def _normalize(value: str) -> str:
    return (
        value.casefold()
        .replace("ı", "i").replace("ş", "s").replace("ğ", "g")
        .replace("ü", "u").replace("ö", "o").replace("ç", "c")
    )


def _has(text: str, *terms: str) -> bool:
    return any(term in text for term in terms)


def build_operational_findings(
    *, question: str, known_facts: Mapping[str, Any] | None = None,
    jurisdiction_ids: Sequence[str] = (), documents: Sequence[Any] = (),
) -> tuple[tuple[OperationalFinding, ...], tuple[str, ...]]:
    text = _normalize(question)
    known = known_facts or {}
    status: EvidenceStatus = "document_backed" if documents else "hypothesis"
    findings: list[OperationalFinding] = []
    unknowns: list[str] = []

    if _has(text, "maden", "ruhsat", "arama projesi", "ocak"):
        findings.append(OperationalFinding(
            "technical_regulatory_process", "maden ruhsat akışı",
            "Ruhsat, izin, çevresel/teknik onay ve saha işletim aşamaları ilgili idare ve teknik koşullara göre ayrıştırılmalıdır.",
            status, ("görevli idare ve işlem zinciri", "izin koşullarının maddi olaya uygulanması", "teknik ihlal ile hukuki sonuç arasındaki nedensellik"), "orta",
        ))
        unknowns.extend(("Ruhsatın aşaması, izin veren idareler ve teknik raporlar", "Saha faaliyeti, güvenlik önlemleri ve olay kronolojisi"))

    if _has(text, "iban", "kripto", "cold wallet", "soguk cuzdan", "borsa", "stablecoin"):
        findings.extend((
            OperationalFinding(
                "financial_crypto_flow", "IBAN-kripto işlem zinciri",
                "Para girişinin IBAN, aracı hesap, borsa dönüşümü ve cüzdan transferi aşamaları işlem zaman çizelgesiyle doğrulanmalıdır; kişi profili veya ekonomik statüden sonuç çıkarılamaz.",
                status, ("delil zinciri ve illiyet", "hesap/cihaz/işlem kayıtlarının ispat değeri", "kast, iştirak veya haksız edinim iddiasının somut fiillere bağlanması"), "orta",
            ),
            OperationalFinding(
                "behavioural_process", "aracı hesap ve erişim davranışı",
                "Hesap/hat sahipliği ile fiili kullanıcı, talimat veren, transferi yapan ve yarar sağlayan kişi ayrıştırılmalıdır; bunlar doğrulanması gereken rol hipotezleridir.",
                "verification_required", ("fail ve iştirak nitelendirmesi", "dijital izlerin korunması", "mağdur zararının ve geri alma imkanının hesabı"), "düşük",
            ),
        ))
        unknowns.extend(("Banka, GSM, borsa, IP/cihaz ve cüzdan zaman çizelgesi", "Fiili kullanıcı ile hesap sahibi arasındaki talimat ve menfaat ilişkisi"))

    if _has(text, "veri ihlali", "siber", "yetkisiz erisim", "fidye", "log", "incident"):
        findings.append(OperationalFinding(
            "cybersecurity_incident", "siber olay ve müdahale akışı",
            "Erişim yetkisi, loglama, tespit, izolasyon, bildirim ve iyileştirme adımları teknik akış olarak ayrı ayrı doğrulanmalıdır.",
            status, ("veri güvenliği tedbirleri ve bildirim yükümlülüğü", "kusur/öngörülebilirlik ve nedensellik", "delil koruma ve olay sonrası işlem"), "orta",
        ))
        unknowns.append("Olay tespit zamanı, log bütünlüğü, erişim yetkileri ve müdahale/bildirim kayıtları")

    if "rekabet" in {_normalize(item) for item in jurisdiction_ids} or _has(text, "pazar", "dagitim", "fiyatlama", "rakip", "tedarikci"):
        findings.append(OperationalFinding(
            "commercial_market_operations", "pazar ve ticari zincir",
            "Ürün/hizmet pazarı, rakipler, tedarikçiler, müşteriler, dağıtım kanalı, fiyat ve dönemsel hacim/ciro akışı ekonomik olgu katmanı olarak incelenmelidir.",
            status, ("ilgili ürün/coğrafi pazar", "pazar gücü ve dışlayıcı/koordineli etki", "ticari uygulamanın rekabetçi etkisi"), "orta",
        ))
        unknowns.append("Yıllara göre pazar payı, satış hacmi/ciro ve pazar tanımı verileri")

    if not findings:
        findings.append(OperationalFinding(
            "general_event_flow", "maddi olay akışı",
            "Olayın fiili adımları, normal işleyiş/teamül ve karar noktaları hukuki unsurlarla eşleştirilmeden kesin sonuç kurulamaz.",
            "verification_required", ("vakıa, delil, nedensellik ve kusur incelemesi",), "düşük",
        ))
        unknowns.append("Olay kronolojisi, ilgili iş akışı/teamül ve bunu doğrulayan belgeler")

    return tuple(findings), tuple(dict.fromkeys(item for item in unknowns if item not in known))
