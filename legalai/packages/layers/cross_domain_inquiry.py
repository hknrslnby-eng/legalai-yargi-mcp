"""Cross-domain legal inquiry scaffolding."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from legalai.packages.shared.types import Document


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


@dataclass(frozen=True)
class CrossDomainBranch:
    domain_id: str
    positive_effects: tuple[str, ...]
    negative_effects: tuple[str, ...]
    cross_domain_effects: tuple[str, ...]


@dataclass(frozen=True)
class CrossDomainInquiry:
    question: str
    detected_domains: list[str]
    allowed_document_ids: list[str]
    branches: list[CrossDomainBranch]

    def render(self) -> str:
        lines = [
            "Cross-domain inquiry",
            f"Question: {self.question}",
            f"Detected domains: {', '.join(self.detected_domains) or '(none)'}",
            "Allowed documents: "
            + (", ".join(f"#{doc_id}" for doc_id in self.allowed_document_ids) or "(none)"),
        ]
        for branch in self.branches:
            lines.extend(
                [
                    "",
                    f"Domain: {branch.domain_id}",
                    "Positive effects:",
                    *[f"- {item}" for item in branch.positive_effects],
                    "Negative effects:",
                    *[f"- {item}" for item in branch.negative_effects],
                    "Cross-domain evidence/argument effects:",
                    *[f"- {item}" for item in branch.cross_domain_effects],
                ]
            )
        return "\n".join(lines)


def build_cross_domain_inquiry(question, jurisdiction_ids, documents=()) -> CrossDomainInquiry:
    """Build a deterministic cross-domain inquiry outline from supplied domains/documents."""
    domains = _unique(jurisdiction_ids)
    document_ids = [document.id for document in documents if isinstance(document, Document) and document.id]
    branches = [
        CrossDomainBranch(
            domain_id=domain_id,
            positive_effects=(
                f"{domain_id} alaninda mevcut olgular talebi destekleyebilir.",
            ),
            negative_effects=(
                f"{domain_id} alaninda eksik unsur, istisna veya karsi yorum sonucu zayiflatabilir.",
            ),
            cross_domain_effects=(
                f"{domain_id} alanindaki delil veya arguman diger alanlarda hem destekleyici hem sinirlayici etki dogurabilir.",
            ),
        )
        for domain_id in domains
    ]
    return CrossDomainInquiry(
        question=question,
        detected_domains=domains,
        allowed_document_ids=document_ids,
        branches=branches,
    )
