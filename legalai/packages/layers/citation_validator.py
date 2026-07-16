"""alinti_dogrula — host modelin (API key gerektirmeyen mod) kendi
taslak cevabındaki `[#doc_id]` referanslarını, gerçek belge kimlikleriyle
kendi kendine kontrol edebilmesi için sunulan SAF PYTHON yardımcı.

Bkz. FORK-KAPSAMLI-PLAN.md Hafta 7/8 pivotu: `VerifiedCitationCheck`'in
"reddet ve tekrar dene" mantığı bir LLM çağrısı GEREKTİRMEZ — sadece
regex + küme üyeliği kontrolüdür. Bu modül, o mantığı `GroundedGenerator`
katmanının dışında, host-orkestrasyonlu (API key'siz) akışlarda da
(derin araştırma, dilekçe oluşturma) tekrar kullanılabilir hale getirir.
"""
from __future__ import annotations

from dataclasses import dataclass

from legalai.packages.layers.verified_citation_check import extract_citations


@dataclass
class CitationValidationResult:
    citations: list[str]
    invalid_citations: list[str]
    valid: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "citations": self.citations,
            "invalid_citations": self.invalid_citations,
            "valid": self.valid,
        }


def validate_citations(answer: str, known_doc_ids: list[str]) -> CitationValidationResult:
    """`answer` içindeki `[#id]` referanslarını çıkarır ve `known_doc_ids`
    kümesiyle karşılaştırır. `invalid_citations` boşsa `valid=True`."""
    known = set(known_doc_ids)
    citations = extract_citations(answer)
    invalid = [c for c in citations if c not in known]
    return CitationValidationResult(citations=citations, invalid_citations=invalid, valid=not invalid)
