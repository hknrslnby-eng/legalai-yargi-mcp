"""Visible operational-context cards for fact-sensitive legal analysis."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


ALLOWED_LABELS = frozenset(
    {
        "operasyonel hipotez",
        "kullanıcı beyanı",
        "belgeyle desteklenen olgu",
        "doğrulama gerekli",
    }
)
CATEGORIES = (
    "actors",
    "workflow",
    "incentives",
    "technical_traces",
    "unlawful_patterns",
    "alternative_explanations",
)


@dataclass(frozen=True)
class OperationalCard:
    category: str
    label: str
    text: str
    jurisdiction_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()


def _has_any(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def build_operational_cards(
    question: str,
    jurisdiction_ids: Iterable[str],
    supplied_facts: Iterable[str] = (),
) -> tuple[OperationalCard, ...]:
    """Build cautious, visibly labelled workflow hypotheses without proving facts."""
    lowered = (question or "").casefold()
    jurisdictions = tuple(dict.fromkeys(item for item in jurisdiction_ids if item))
    facts = tuple(fact.strip() for fact in supplied_facts if str(fact).strip())
    crypto = _has_any(lowered, ("iban", "kripto", "cüzdan", "cuzdan", "token"))
    market = _has_any(lowered, ("dağıtım", "dagitim", "bayi", "pazar", "fiyat", "sözleşme", "sozlesme"))
    technical = _has_any(lowered, ("bilirkişi", "bilirkisi", "log", "sunucu", "zaman damgası", "zaman damgasi", "kalibrasyon"))
    user_stated = _has_any(lowered, ("gönderdim", "gonderdim", "yaşadım", "yasadim", "aldım", "aldim"))
    fact_label = "belgeyle desteklenen olgu" if facts else "kullanıcı beyanı"
    if not (crypto or market or technical):
        fact_label = "doğrulama gerekli"

    domain_text = "Aktörler, üçüncü kişiler ve olayın doğrulanması gereken karar noktaları"
    if market:
        domain_text = "Sözleşme, dağıtım/bayi ve pazar aktörleri"
    if technical:
        domain_text = "Raporu düzenleyenler, veri sağlayıcılar ve teknik sistem aktörleri"
    workflow_text = (
        "Para transferi, cüzdan yönlendirmesi ve kayıt izi oluşturma adımları incelenmeli."
        if crypto
        else "Sözleşme kurulumu, ifa, fiyatlama ve pazar uygulaması adımları ayrıştırılmalı."
        if market
        else "Raporun veri toplama, ölçüm, hesaplama ve sonuçlandırma adımları yeniden kurulmalı."
        if technical
        else "Olayın önce-sonra akışı ve karar noktaları kullanıcıdan doğrulanmalı."
    )
    technical_text = (
        "IBAN, cüzdan adresi, işlem zamanları ve cihaz/hesap logları karşılaştırılmalı."
        if crypto
        else "Fiyat listeleri, bayi yazışmaları, sözleşme sürümleri ve pazar verileri karşılaştırılmalı."
        if market
        else "Log, zaman damgası, ham veri, yöntem, kalibrasyon ve hata payı incelenmeli."
        if technical
        else "Belge, kayıt veya bağımsız teknik iz bulunup bulunmadığı doğrulanmalı."
    )
    texts = {
        "actors": domain_text,
        "workflow": workflow_text,
        "incentives": "Aktörlerin ekonomik, ticari, teknik veya hukuki teşvikleri yalnızca hipotez olarak test edilmeli.",
        "technical_traces": technical_text,
        "unlawful_patterns": "Eylem örüntüsü, hukuka aykırılık varsayımı olarak değil; alternatif açıklamalarla birlikte araştırılmalı.",
        "alternative_explanations": "Masum hata, olağan ticari/teknik süreç, üçüncü kişi etkisi ve veri eksikliği alternatifleri ayrıca sınanmalı.",
    }
    labels = {
        "actors": "kullanıcı beyanı" if user_stated else ("operasyonel hipotez" if crypto or market or technical else "doğrulama gerekli"),
        "workflow": "operasyonel hipotez" if crypto or market or technical else "doğrulama gerekli",
        "incentives": "operasyonel hipotez",
        "technical_traces": fact_label if facts and technical else "doğrulama gerekli",
        "unlawful_patterns": "operasyonel hipotez",
        "alternative_explanations": "doğrulama gerekli",
    }
    return tuple(
        OperationalCard(category, labels[category], texts[category], jurisdictions)
        for category in CATEGORIES
    )
