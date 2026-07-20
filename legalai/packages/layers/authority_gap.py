"""Otorite boÅŸluÄŸu ve kÄ±yas kontrolÃ¼ iÃ§in yapÄ±landÄ±rÄ±lmÄ±ÅŸ Ã§Ä±ktÄ±.

Arama sonucunun bulunmasÄ±, bir kaynaÄŸÄ±n somut olaya doÄŸrudan uygulandÄ±ÄŸÄ±nÄ±
ispatlamaz. Bu modÃ¼l, doÄŸrudan otorite bulunmadÄ±ÄŸÄ±nda modelin kÄ±yas,
amaÃ§sal yorum ve anayasal sÄ±nÄ±rlarÄ± ayrÄ± gÃ¶stermesini saÄŸlayan denetlenebilir
bir sÃ¶zleÅŸme Ã¼retir; yeni hukuk kuralÄ± veya karar uydurmaz.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from legalai.packages.shared.types import Document


@dataclass(frozen=True)
class AnalogyCandidate:
    source_id: str
    citation: str
    source: str
    similarity_axes: tuple[str, ...] = (
        "norm veya hukuki unsur",
        "maddi vakÄ±a ve delil yapÄ±sÄ±",
        "korunan menfaat ve hukuki amaÃ§",
    )
    distinctions_to_check: tuple[str, ...] = (
        "kaynaÄŸÄ±n baÄŸlayÄ±cÄ±lÄ±k seviyesi ve yargÄ± tÃ¼rÃ¼",
        "olay, dava ve yÃ¼rÃ¼rlÃ¼k tarihleri",
        "somut olayÄ±n farklÄ± maddi/teknik unsurlarÄ±",
    )
    permissible_use: str = "KÄ±yas iÃ§in aday; doÄŸrudan emsal veya baÄŸlayÄ±cÄ± kural deÄŸildir."
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "citation": self.citation,
            "source": self.source,
            "similarity_axes": list(self.similarity_axes),
            "distinctions_to_check": list(self.distinctions_to_check),
            "permissible_use": self.permissible_use,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class AuthorityGapAssessment:
    direct_authority_status: str
    direct_authority_note: str
    candidate_source_ids: tuple[str, ...] = ()
    analogy_required: bool = True
    analogy_method: tuple[str, ...] = (
        "Önce doğrudan uygulanabilir norm, yerleşik içtihat veya açık kurum yetkisi ara.",
        "Sonra aday kaynağın norm, unsur, amaç ve maddi vakıa benzerliğini ayrı ayrı karşılaştır.",
        "Farklılıkları, bağlayıcılık seviyesini ve kıyasın hukuken izin verilen sınırını açıkla.",
        "Sonucu kesin hüküm değil, koşullu ve doğrulanması gereken hukuki değerlendirme olarak yaz.",
    )
    legal_limits: tuple[str, ...] = (
        "Ceza hukukunda kanunilik ve aleyhe kıyas yasağını kontrol et.",
        "Vergi hukukunda kanunilik ve verginin kanuniliği ilkelerini kontrol et.",
        "Temel hak sınırlamalarında kanunilik, meşru amaç, gereklilik ve ölçülülüğü kontrol et.",
    )
    candidates: tuple[AnalogyCandidate, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "direct_authority_status": self.direct_authority_status,
            "direct_authority_note": self.direct_authority_note,
            "candidate_source_ids": list(self.candidate_source_ids),
            "analogy_required": self.analogy_required,
            "analogy_method": list(self.analogy_method),
            "legal_limits": list(self.legal_limits),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "analysis_only": True,
            "non_binding": True,
        }


def assess_authority_gap(
    documents: Sequence[Document], jurisdiction_ids: Sequence[str] = ()
) -> AuthorityGapAssessment:
    """Arama çıktısını doğrudan otorite iddiasına dönüştürmeden sınıflandırır.

    Exact applicability ancak modelin belge metni, olay ve norm unsurlarını
    karşılaştırmasıyla belirlenebilir. Bu nedenle ``candidate`` etiketini
    kullanır ve her belge için kıyas kontrolü ister.
    """
    candidates = tuple(
        AnalogyCandidate(
            source_id=document.id,
            citation=document.citation,
            source=document.source,
        )
        for document in documents
    )
    ids = tuple(document.id for document in documents)
    status = "no_direct_source_retrieved" if not documents else "direct_applicability_not_established"
    note = (
        "Arama sonucu yok; doğrudan otorite bulunamadı. Mevzuat ve resmi kaynaklarda yeni arama gerekir."
        if not documents
        else "Kaynak adayları bulundu; bunların somut olaya doğrudan uygulanabilirliği ayrıca doğrulanmalıdır."
    )
    # The parameter is deliberately consumed here so callers can pass detected
    # multi-domain context without changing the conservative classification.
    del jurisdiction_ids
    return AuthorityGapAssessment(
        direct_authority_status=status,
        direct_authority_note=note,
        candidate_source_ids=ids,
        candidates=candidates,
    )


def build_authority_gap_instructions(
    source_ids: Sequence[str] = (), jurisdiction_ids: Sequence[str] = ()
) -> str:
    """Host modele, kaynak yokluğunda güvenli hukuk kurma yönergesi verir."""
    ids = ", ".join(f"#{source_id}" for source_id in source_ids) or "(aday kaynak yok)"
    domains = ", ".join(dict.fromkeys(jurisdiction_ids)) or "algılanan alanlar"
    return (
        "OTORİTE BOŞLUĞU VE KIYAS KONTROLÜ\n"
        f"İlgili alanlar: {domains}. Aday kaynaklar: {ids}.\n"
        "Doğrudan uygulanabilir ve bağlayıcı bir norm/içtihat bulunmadığında bunu açıkça belirt; "
        "yalnızca erişilen kaynaklardan hareketle norm-unsur-amaç-vakıa benzerliğini ve farklarını "
        "ayrı bir tabloda göster. Kıyasın hukuken izin verilen/izin verilmeyen yönlerini açıklamadan "
        "'emsal', 'kesin kural' veya 'yerleşik görüş' deme. Ceza ve vergi hukukunda kanunilik ve "
        "kıyas sınırlarını; temel haklarda kanunilik, meşru amaç, gereklilik ve ölçülülüğü ayrıca kontrol et. "
        "Kaynak, madde, karar veya alıntı uydurma. Sonucu koşullu, analysis-only ve non-binding sun."
    )
