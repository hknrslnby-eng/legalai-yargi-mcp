"""Görev, yetki, icra/kurum ve zorunlu ön şart adaylarını üretir."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import unicodedata

from legalai.packages.jurisdictions.base import JurisdictionProfile
from legalai.packages.shared.evidence import EvidenceBlock, SourceScope, validate_source_scope
from legalai.packages.shared.temporal import TemporalLegalContext


@dataclass
class ForumCandidate:
    kind: str
    name: str
    jurisdiction_basis: str
    venue_basis: str
    prerequisites: list[str] = field(default_factory=list)
    deadline_risks: list[Any] = field(default_factory=list)
    evidence: list[EvidenceBlock] = field(default_factory=list)
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "name": self.name,
            "jurisdiction_basis": self.jurisdiction_basis,
            "venue_basis": self.venue_basis,
            "prerequisites": self.prerequisites,
            "deadline_risks": [getattr(item, "__dict__", item) for item in self.deadline_risks],
            "evidence": [item.to_dict() for item in self.evidence],
            "confidence": self.confidence,
            "assumptions": self.assumptions,
        }


class ForumAndDeadlineAnalyzer:
    def analyze(
        self,
        question: str,
        context: TemporalLegalContext | None,
        profile: JurisdictionProfile,
        documents: list[Any] | None = None,
        source_scope: SourceScope = "targeted",
        selected_source_ids: list[str] | None = None,
    ) -> list[ForumCandidate]:
        validate_source_scope(source_scope)
        if source_scope == "selected" and not selected_source_ids:
            selection_assumption = "Seçili kaynak kimlikleri verilmedi; adaylar profil/olay sinyalleriyle sınırlı üretildi."
        else:
            selection_assumption = ""

        lower = _normalize_text(question)
        candidates: list[ForumCandidate] = []
        profile_forums = profile.raw.get("competent_forums", []) if profile.raw else []
        for raw in profile_forums:
            if isinstance(raw, str):
                raw = {"kind": "mahkeme", "name": raw, "basis": "jurisdiction profile"}
            candidates.append(
                ForumCandidate(
                    kind=str(raw.get("kind", "mahkeme")),
                    name=str(raw.get("name", "Profilde belirtilen merci")),
                    jurisdiction_basis=str(raw.get("basis", "jurisdiction profile")),
                    venue_basis="Yerleşim/ifa/işlem yeri ayrıca doğrulanmalı.",
                    prerequisites=list(raw.get("prerequisites", [])),
                    confidence=0.55,
                    assumptions=["Profil adayıdır; somut görev ve yetki vakıaları eksik olabilir."],
                )
            )

        if any(token in lower for token in ("alacak", "alaca", "borc", "fatura", "sozlesme")):
            candidates.extend(
                [
                    ForumCandidate(
                        "icra_dairesi",
                        "Yetkili icra dairesi",
                        "Alacağın niteliği ve takip türü",
                        "Borçlunun yerleşim yeri/ifa yeri ve özel yetki kuralları",
                        confidence=0.45,
                        assumptions=["Takip türü, belge ve yetki sözleşmesi incelenmedi."],
                    ),
                    ForumCandidate(
                        "arabuluculuk",
                        "Arabuluculuk bürosu veya ihtiyari arabuluculuk",
                        "Uyuşmazlığın konusu ve dava şartı kapsamı",
                        "Yetkili arabuluculuk bürosu ve başvuru yeri ayrıca doğrulanmalı",
                        prerequisites=["Uyuşmazlığın zorunlu arabuluculuk kapsamında olup olmadığı"],
                        confidence=0.4,
                        assumptions=["Dava şartı kapsamı somut uyuşmazlık türüne göre kontrol edilmeli."],
                    ),
                ]
            )

        if any(token in lower for token in ("idare", "idari islem", "ruhsat", "vergi")):
            candidates.extend(
                [
                    ForumCandidate(
                        "idari_kurum",
                        "İlgili idari kurum veya kurul",
                        "İşlemi tesis eden kurum/kurul",
                        "Başvuru ve itiraz mercii mevzuata göre doğrulanmalı",
                        confidence=0.4,
                        assumptions=["İşlemin niteliği ve özel başvuru yolu bilinmiyor."],
                    ),
                    ForumCandidate(
                        "mahkeme",
                        "Yetkili idare mahkemesi",
                        "İşlemin idari yargı denetimine tabi olduğu varsayımı",
                        "İşlemi yapan merciin bulunduğu yer ve özel yetki kuralları",
                        prerequisites=["Dava açma süresi ve varsa zorunlu idari başvuru"],
                        confidence=0.35,
                        assumptions=["İdari yargı görev alanı kesinleştirilmedi."],
                    ),
                ]
            )

        evidence = _document_evidence(documents or [])
        for candidate in candidates:
            candidate.evidence.extend(evidence)
            if selection_assumption:
                candidate.assumptions.append(selection_assumption)
            if context and context.missing_facts:
                candidate.assumptions.append("Tarih/olay ayrıntıları eksik; süre ve yetki sonucu kesin değildir.")

        if not candidates:
            candidates.append(
                ForumCandidate(
                    "mahkeme",
                    "Görevli ve yetkili merci adayı",
                    "Somut hukuki ilişkinin niteliği belirlenemedi",
                    "Yer ve taraf bilgileri gerekli",
                    confidence=0.15,
                    assumptions=["Soruda görev/yetki analizi için yeterli olay bilgisi yok."],
                )
            )
        return sorted(candidates, key=lambda item: item.confidence, reverse=True)


def _document_evidence(documents: list[Any]) -> list[EvidenceBlock]:
    evidence: list[EvidenceBlock] = []
    for document in documents:
        body = str(getattr(document, "body", "")).strip()
        if not body:
            continue
        evidence.append(
            EvidenceBlock(
                claim="Belge, görev/yetki değerlendirmesinde incelenebilecek içerik taşıyor.",
                source_type=str(getattr(document, "source", "document")),
                citation_key=str(getattr(document, "id", "")),
                full_citation=str(getattr(document, "citation", "")),
                short_quote=body[:240],
                document_id=str(getattr(document, "id", "")),
                temporal_status="document-date-not-resolved",
                relevance="medium",
                confidence=0.35,
            )
        )
    return evidence


def _normalize_text(value: str) -> str:
    """Normalize proper Turkish and legacy mojibake client input alike."""
    text = value
    for _ in range(2):
        try:
            repaired = text.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if repaired == text:
            break
        text = repaired
    return "".join(
        char for char in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(char)
    )
