"""Shared quality guardrails for every general pleading operation."""
from __future__ import annotations

from typing import Any

from legalai.packages.layers.cross_domain_inquiry import build_cross_domain_inquiry
from legalai.packages.layers.operational_context import OperationalContextBuilder
from legalai.packages.layers.quality_contract import build_quality_contract
from legalai.packages.layers.quality_policy import build_quality_context
from legalai.packages.shared.types import Document


def build_petition_quality(
    question: str,
    jurisdiction_hint: str | None,
    source_documents: list[dict[str, Any]],
    detail_level: str,
) -> dict[str, Any]:
    domains = [part.strip() for part in (jurisdiction_hint or "hukuk").replace("/", ",").split(",") if part.strip()]
    documents = [
        Document(
            id=str(item.get("id", "")),
            body=str(item.get("quote", "")),
            source=str(item.get("source", "user-supplied")),
            citation=str(item.get("citation", "")),
        )
        for item in source_documents
        if item.get("id")
    ]
    inquiry = build_cross_domain_inquiry(question, domains, documents)
    operational = OperationalContextBuilder().build(question, domains)
    source_ids = tuple(document.id for document in documents)
    return {
        "turkish_language_professor_lens": True,
        "language_instruction": "Türkçe hukuk dili profesörü perspektifi: açık, tutarlı, duru ve hukuki anlamı değiştirmeyen yazım.",
        "detail_level": detail_level,
        "quality_contract": build_quality_contract("frontier" if detail_level in {"deep", "exhaustive"} else "balanced", source_ids=source_ids),
        "quality_policy": build_quality_context(domains, ["kıdemli hukukçu", "Türkçe dil profesörü"], source_ids, operational),
        "cross_domain_inquiry": inquiry,
        "operational_context": operational,
    }
