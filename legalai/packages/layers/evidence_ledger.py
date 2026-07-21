"""Source-grounded evidence ledger with explicit unsupported-citation states."""
from __future__ import annotations

from typing import Any, Iterable

from legalai.packages.shared.evidence import EvidenceRecord
from legalai.packages.shared.types import Document


def _metadata(document: Document, key: str, default: str = "") -> str:
    value = (document.metadata or {}).get(key, default)
    return str(value) if value is not None else default


def build_evidence_ledger(
    claims: Iterable[dict[str, Any]],
    documents: Iterable[Document],
    source_evidence: Iterable[dict[str, Any]] = (),
) -> tuple[EvidenceRecord, ...]:
    by_id = {document.id: document for document in documents if document.id}
    overrides = {(item.get("claim_id"), item.get("source_id")): item for item in source_evidence}
    records: list[EvidenceRecord] = []
    for claim in claims:
        claim_id = str(claim.get("id") or claim.get("claim_id") or "")
        source_ids = claim.get("source_ids") or []
        for source_id in source_ids:
            source_id = str(source_id)
            document = by_id.get(source_id)
            extra = overrides.get((claim_id, source_id), {})
            body = document.body.strip() if document else ""
            records.append(
                EvidenceRecord(
                    claim_id=claim_id,
                    source_id=source_id,
                    source_type=document.source if document else "unknown",
                    full_citation=document.citation if document else "",
                    short_quote=body[:300] if body else "",
                    page=_metadata(document, "page") if document else "",
                    paragraph=_metadata(document, "paragraph") if document else "",
                    pin=str(extra.get("pin") or _metadata(document, "pin")) if document else str(extra.get("pin") or ""),
                    authority_level=_metadata(document, "authority_level") if document else "",
                    ratio_or_dictum=str(extra.get("ratio_or_dictum") or ""),
                    temporal_note=str(claim.get("temporal_note") or ""),
                    relevance=str(extra.get("relevance") or claim.get("relevance") or "medium"),
                    supported=document is not None and bool(body),
                )
            )
    return tuple(records)


def validate_evidence_ledger(records: Iterable[EvidenceRecord]) -> dict[str, Any]:
    items = tuple(records)
    unsupported = [record.source_id for record in items if not record.full_citation]
    empty_quotes = [record.source_id for record in items if not record.short_quote and record.full_citation]
    return {
        "valid": not unsupported and not empty_quotes,
        "unsupported_citations": unsupported,
        "empty_quote_source_ids": empty_quotes,
        "analysis_only": True,
        "non_binding": True,
    }
