"""Deterministic pleading router; host models perform the final prose synthesis."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from .models import PetitionRequest, PetitionResult
from .quality import build_petition_quality
from legalai.packages.shared.evidence import EvidenceRecord

_PROTECTED = {
    "dava şartı": ("dava şartı", "dava sarti"),
    "görev": ("görev", "gorev"),
    "kesin yetki": ("kesin yetki", "kesin yetki"),
    "süre": ("süre", "sure", "hak düşürücü", "zamanaşımı"),
    "delil": ("delil", "bilirkişi", "tanık"),
    "talep sonucu": ("talep sonucu", "sonuç ve istem", "sonuc ve istem"),
}


def process_petition(request: PetitionRequest) -> PetitionResult:
    if request.operation not in {"draft", "review", "shorten", "lengthen"}:
        raise ValueError("operation draft, review, shorten veya lengthen olmalıdır.")
    if request.operation != "draft" and not (request.petition_text or "").strip():
        raise ValueError("Bu işlem için petition_text gereklidir.")

    text = request.petition_text or ""
    quality = build_petition_quality(request.question, request.jurisdiction_hint, request.source_documents, request.detail_level)
    domains = quality["cross_domain_inquiry"].detected_domains
    operational = quality["operational_context"]
    protected = _protected_topics(text)
    paragraphs = _classify_paragraphs(text)
    sections = _draft_sections(request)
    changes: list[dict[str, Any]] = []

    if request.operation == "review":
        changes = [item for item in paragraphs if item["classification"] in {"duplicative", "risky_or_procedural"}]
        summary = "Dilekçe; hukuki koruma konuları korunarak tekrar, eksik dayanak ve usuli riskler bakımından incelenmelidir."
    elif request.operation == "shorten":
        changes = _shortening_changes(paragraphs, protected)
        summary = "Kısaltma önerileri ana vakıa, usul güvenceleri, delil ve talep sonucu korunacak şekilde sunulmuştur; silme kullanıcı onayına bağlıdır."
    elif request.operation == "lengthen":
        changes = _lengthening_changes(request.source_documents)
        summary = "Uzatma yalnızca verilen kaynaklar, mevcut vakıalar ve doğrulanabilir hukuki bağlantılarla sınırlı tutulmalıdır."
    else:
        summary = "Kaynak, olay ve talep bilgileri tamamlandığında host model bu iskeleti kaynaklı dilekçeye dönüştürebilir."

    inquiry = quality["cross_domain_inquiry"].render()
    evidence_ledger = [
        EvidenceRecord(
            claim_id="petition-allowed-source",
            source_id=str(item.get("id")),
            source_type=str(item.get("source", "user-supplied")),
            full_citation=str(item.get("citation", "")),
            short_quote=str(item.get("quote", "")),
            relevance="high",
            supported=bool(item.get("citation") and item.get("quote")),
        ).to_dict()
        for item in request.source_documents
        if item.get("id")
    ]
    return PetitionResult(
        operation=request.operation,
        executive_summary=summary,
        sections=sections,
        paragraphs=paragraphs,
        changes=changes,
        protected_topics=protected,
        shortening_safeguards={
            "requires_user_confirmation": request.operation == "shorten",
            "protected_topics": sorted(protected),
            "never_silent_delete": True,
        },
        lengthening_safeguards={
            "new_facts_allowed": False,
            "only_supplied_sources": True,
            "source_ids": [str(item.get("id")) for item in request.source_documents if item.get("id")],
        },
        quality={**{key: value for key, value in quality.items() if key not in {"cross_domain_inquiry", "operational_context"}}, "cross_domain_instruction": inquiry},
        source_requirements={
            "citation_and_quote_required": True,
            "allowed_source_ids": [str(item.get("id")) for item in request.source_documents if item.get("id")],
            "unsupported_claim_action": "kaynak yoksa açıkça doğrulama gerekli olarak işaretle; künye veya alıntı uydurma",
        },
        evidence_ledger=evidence_ledger,
        operational_cards=quality["operational_cards"],
        cross_domain_inquiry={
            "question": quality["cross_domain_inquiry"].question,
            "detected_domains": domains,
            "branches": [
                {"domain_id": branch.domain_id, "positive_effects": list(branch.positive_effects), "negative_effects": list(branch.negative_effects), "cross_domain_effects": list(branch.cross_domain_effects)}
                for branch in quality["cross_domain_inquiry"].branches
            ],
        },
        operational_context=operational.to_dict(),
        temporal_context={
            "event_dates": list(request.event_dates or []),
            "instruction": "Olay, tebliğ, dava ve yürürlük tarihleri doğrulanmadan süre veya uygulanacak hukuk sonucu kesinleştirilmemeli.",
        },
        missing_facts=_missing_facts(request, text),
    )


def _draft_sections(request: PetitionRequest) -> list[dict[str, Any]]:
    return [
        {"id": "merci", "title": "Görevli/yetkili merci", "required": True},
        {"id": "taraflar", "title": "Taraflar ve sıfatları", "required": True},
        {"id": "olaylar", "title": "Maddi vakıalar ve kronoloji", "required": True},
        {"id": "hukuki_nedenler", "title": "Hukuki sorun, normlar, içtihat ve doktrin bağlantıları", "required": True},
        {"id": "deliller", "title": "Deliller ve karşı argümanlara cevap", "required": True},
        {"id": "sure_ve_usul", "title": "Süre, dava şartı, görev, kesin yetki ve usul riskleri", "required": True},
        {"id": "talep_sonucu", "title": "Sonuç ve istem", "required": True},
        {"id": "kaynakca", "title": "Künye, kısa alıntı ve kaynakça", "required": True},
    ]


def _protected_topics(text: str) -> set[str]:
    lowered = _fold(text)
    return {label for label, terms in _PROTECTED.items() if any(_fold(term) in lowered for term in terms)}


def _fold(value: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(char))


def _classify_paragraphs(text: str) -> list[dict[str, Any]]:
    paragraphs = [item.strip() for item in re.split(r"\n+", text) if item.strip()]
    seen: dict[str, int] = {}
    result = []
    for index, paragraph in enumerate(paragraphs, 1):
        key = " ".join(paragraph.casefold().split())
        duplicate = key in seen
        seen[key] = index
        lower = paragraph.casefold()
        procedural = any(term in lower for term in ("dava şartı", "görev", "yetki", "süre", "delil", "sonuç ve istem", "talep sonucu"))
        result.append({"paragraph_index": index, "text": paragraph, "classification": "duplicative" if duplicate else "risky_or_procedural" if procedural else "essential", "protected": procedural})
    return result


def _shortening_changes(paragraphs: list[dict[str, Any]], protected: set[str]) -> list[dict[str, Any]]:
    changes = []
    for item in paragraphs:
        if item["classification"] == "duplicative":
            changes.append({"paragraph_index": item["paragraph_index"], "action": "propose_delete_after_confirmation", "reason": "Tekrar içeriyor; bağlam korunarak birleştirilebilir."})
        elif item["protected"]:
            changes.append({"paragraph_index": item["paragraph_index"], "action": "preserve", "reason": "Dava şartı/görev/yetki/süre/delil/talep sonucu güvenlik alanı."})
    return changes


def _lengthening_changes(source_documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not source_documents:
        return [{"paragraph_index": 0, "action": "request_sources", "reason": "Norm, içtihat veya doktrin alıntısı eklemek için doğrulanabilir kaynak gerekir."}]
    return [{"paragraph_index": 0, "action": "add_source_linked_argument", "source_id": str(item.get("id")), "reason": "Yalnızca künyesi ve alıntısı verilen kaynakla hukuki bağlantı kurulabilir."} for item in source_documents if item.get("id")]


def _missing_facts(request: PetitionRequest, text: str) -> list[str]:
    missing = []
    if not request.jurisdiction_hint:
        missing.append("Yargı türü, görevli ve yetkili merci")
    if not request.event_dates:
        missing.append("Olay, tebliğ, dava ve ilgili yürürlük tarihleri")
    if not text.strip() and request.operation == "draft":
        missing.append("Maddi vakıa ve talep anlatımı")
    return missing
