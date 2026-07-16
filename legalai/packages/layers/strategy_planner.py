"""Dava dışı yolları da içeren, koşullu ve kaynaklanabilir çözüm planlayıcısı."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from legalai.packages.layers.forum_analyzer import ForumCandidate
from legalai.packages.shared.evidence import EvidenceBlock, SourceScope, validate_source_scope
from legalai.packages.shared.temporal import TemporalLegalContext


@dataclass
class StrategicPath:
    kind: str
    title: str
    objective: str
    prerequisites: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    evidence: list[EvidenceBlock] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    reversibility: str = "unknown"
    expected_next_action: str = "Eksik vakıaları ve kaynakları doğrula."
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "title": self.title,
            "objective": self.objective,
            "prerequisites": self.prerequisites,
            "steps": self.steps,
            "evidence": [item.to_dict() for item in self.evidence],
            "benefits": self.benefits,
            "risks": self.risks,
            "reversibility": self.reversibility,
            "expected_next_action": self.expected_next_action,
            "confidence": self.confidence,
            "assumptions": self.assumptions,
        }


class StrategicPathPlanner:
    def plan(
        self,
        question: str,
        position: str,
        temporal_context: TemporalLegalContext | None,
        forum_candidates: list[ForumCandidate],
        documents: list[Any] | None = None,
        source_scope: SourceScope = "targeted",
        selected_source_ids: list[str] | None = None,
    ) -> list[StrategicPath]:
        validate_source_scope(source_scope)
        lower = question.lower()
        evidence = _document_evidence(documents or [])
        assumptions = [f"Pozisyon rolü: {position}; karşı taraf ve olay vakıaları ayrıca doğrulanmalı."]
        if temporal_context and temporal_context.missing_facts:
            assumptions.append("Tarih veya kaynak bilgisi eksik; sıralama ve süre sonucu kesin değildir.")
        if source_scope == "selected" and not selected_source_ids:
            assumptions.append("Seçili kaynak listesi verilmedi.")

        paths = [_negotiation(evidence, assumptions)]
        debt_signal = any(token in lower for token in ("alacak", "borç", "fatura", "tahsil"))
        admin_signal = any(token in lower for token in ("idare", "idari işlem", "ruhsat", "vergi"))

        if debt_signal:
            paths.extend(
                [
                    _settlement_35a(evidence, assumptions),
                    _mediation(evidence, assumptions),
                    _enforcement(evidence, forum_candidates, assumptions),
                    _suit(evidence, forum_candidates, assumptions),
                ]
            )
        if admin_signal:
            paths.append(_administrative_application(evidence, assumptions))
            paths.append(_suit(evidence, forum_candidates, assumptions, administrative=True))

        if _concrete_offence_signal(lower):
            paths.append(_criminal_complaint(evidence, assumptions))

        return paths


def _base(kind: str, title: str, objective: str, evidence: list[EvidenceBlock], assumptions: list[str]) -> StrategicPath:
    return StrategicPath(
        kind=kind,
        title=title,
        objective=objective,
        evidence=evidence,
        confidence=0.35 if assumptions else 0.5,
        assumptions=list(assumptions),
    )


def _negotiation(evidence, assumptions):
    path = _base("negotiation", "Müzakere ve gönüllü ödeme", "Uyuşmazlığı hızlı ve kontrollü çözmek", evidence, assumptions)
    path.steps = ["Yetki ve temsil durumunu doğrula", "Teklif, takvim ve temerrüt sonuçlarını yazılılaştır"]
    path.benefits = ["Daha düşük maliyet ve hızlı tahsil ihtimali"]
    path.risks = ["Hak veya delil kaybı yaratacak feragat/ibra ifadelerini kontrol et"]
    path.reversibility = "yüksek"
    path.expected_next_action = "Karşı tarafın ödeme ve uzlaşma kapasitesini ölçen yazılı teklif hazırla."
    return path


def _settlement_35a(evidence, assumptions):
    path = _base("settlement_35a", "Avukatlık Kanunu m.35/A uzlaşması", "Dava öncesi veya uygun aşamada icra edilebilir uzlaşma zemini aramak", evidence, assumptions)
    path.prerequisites = ["Avukatların yetkisi ve gönüllü tasarruf edilebilir hak", "Usulüne uygun uzlaşma tutanağı"]
    path.steps = ["Karşı taraf vekiline yazılı davet ve teklif ilet", "Ödeme/ifa, temerrüt ve uyuşmazlık kapanışını tutanağa bağla", "İcra edilebilirlik etkisini somut metin üzerinden doğrula"]
    path.benefits = ["Dava açılmadan sonuç alma ve icra kabiliyeti ihtimali"]
    path.risks = ["Yetki, şekil ve feragat/ibra kapsamı hatalı kurulabilir"]
    path.reversibility = "orta"
    return path


def _mediation(evidence, assumptions):
    path = _base("mediation", "Zorunlu veya ihtiyari arabuluculuk", "Anlaşma ile uyuşmazlığı sonlandırmak veya dava şartını tamamlamak", evidence, assumptions)
    path.prerequisites = ["Uyuşmazlığın dava şartı arabuluculuk kapsamı", "Tarafların ve temsil yetkisinin doğrulanması"]
    path.steps = ["Kapsamı ve yetkili büroyu kontrol et", "Anlaşma metninde ifa, icra edilebilirlik ve ibra etkisini açıklaştır"]
    path.benefits = ["Dava şartının tamamlanması veya hızlı anlaşma"]
    path.risks = ["Anlaşma metni yanlış kapsamda kesin sonuç veya beklenmeyen feragat doğurabilir"]
    path.reversibility = "düşük"
    return path


def _enforcement(evidence, forums, assumptions):
    path = _base("enforcement", "İcra yoluyla tahsil", "Belgeye ve alacağın niteliğine göre hızlı tahsil denemek", evidence, assumptions)
    path.prerequisites = ["Muaccel ve ispatlanabilir alacak", "Doğru takip türü ve yetkili icra dairesi"]
    path.steps = ["Belge ve muacceliyet kontrolü", "Yetkili icra dairesi ve takip türünü seç", "Tebligat, itiraz ve itirazın kaldırılması/iptali risklerini planla"]
    path.benefits = ["Dava yoluna göre erken tahsil baskısı oluşturabilir"]
    path.risks = ["Yetkisiz takip, itiraz ve kötü niyet tazminatı riskleri"]
    path.reversibility = "orta"
    path.expected_next_action = "Forum adaylarındaki icra dairesi ve belgelere ilişkin eksikleri doğrula."
    return path


def _suit(evidence, forums, assumptions, administrative=False):
    title = "İdari yargı veya görevli mahkemede dava" if administrative else "Görevli ve yetkili mahkemede dava"
    path = _base("suit", title, "Bağlayıcı yargısal karar elde etmek", evidence, assumptions)
    path.prerequisites = ["Görev, yetki, dava şartları ve sürelerin doğrulanması"]
    path.steps = ["Olay kronolojisi ve delil matrisi çıkar", "Görevli/yetkili mahkeme adayını doğrula", "Süre ve zorunlu başvuru risklerini kontrol et"]
    path.benefits = ["Yargısal koruma ve hüküm elde etme imkânı"]
    path.risks = ["Süre, görev, yetki ve ispat eksikliği"]
    path.reversibility = "düşük"
    return path


def _administrative_application(evidence, assumptions):
    path = _base("administrative_application", "İdareye başvuru ve ret kararını koruma", "İdari çözüm, süre koruması ve sonraki sürece dayanak oluşturmak", evidence, assumptions)
    path.prerequisites = ["Özel başvuru/itiraz zorunluluğu ve süre"]
    path.steps = ["İşlemi tesis eden idareye başvur", "Başvuru ve tebliğ tarihlerini belgeyle koru", "Ret veya zımni ret oluşursa sonraki başvuru/dava süresini hesapla"]
    path.benefits = ["İdare içinde çözüm ve sonraki süreç için kayıt oluşturma"]
    path.risks = ["Başvuru dava süresini her durumda durdurmayabilir; özel rejim doğrulanmalı"]
    path.reversibility = "orta"
    return path


def _criminal_complaint(evidence, assumptions):
    path = _base("criminal_complaint", "Somut suç şüphesi varsa ceza başvurusu", "Gerçek bir suç iddiasını yetkili makama bildirmek", evidence, assumptions)
    path.prerequisites = ["Somut suç vakıası ve hukuka uygun delil"]
    path.steps = ["Suç tipini ve zamanaşımını bağımsız doğrula", "Delilleri hukuka uygun biçimde koru", "Ceza sürecini hukukî tahsil stratejisinden ayrı değerlendir"]
    path.benefits = ["Gerçek suç şüphesinin yetkili makamca soruşturulması"]
    path.risks = ["Şikâyet yolu delil toplama aracı olarak kötüye kullanılamaz", "İftira/kişilik hakkı/ceza sorumluluğu riski"]
    path.reversibility = "düşük"
    path.confidence = 0.25
    return path


def _concrete_offence_signal(lower: str) -> bool:
    return any(token in lower for token in ("sahte belge", "dolandırıcılık", "tehdit", "zimmet", "rüşvet"))


def _document_evidence(documents: list[Any]) -> list[EvidenceBlock]:
    result: list[EvidenceBlock] = []
    for document in documents:
        body = str(getattr(document, "body", "")).strip()
        if body:
            result.append(
                EvidenceBlock(
                    claim="Belge, stratejik seçeneklerin değerlendirilmesinde incelenebilir.",
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
    return result
