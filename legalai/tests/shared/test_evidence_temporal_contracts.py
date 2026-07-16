from datetime import date

import pytest

from legalai.packages.shared.evidence import (
    EvidenceBlock,
    LegalAnalysisEnvelope,
    SourceScope,
    validate_source_scope,
)
from legalai.packages.shared.temporal import DateObservation, TemporalLegalContext


def test_evidence_block_serializes_citation_and_temporal_fields() -> None:
    block = EvidenceBlock(
        claim="Norm yürürlüktedir.",
        source_type="mevzuat",
        citation_key="norm-1",
        full_citation="Kanun m. 1",
        short_quote="Bu Kanun yayımlandığı tarihte yürürlüğe girer.",
        source_url="https://example.test/norm-1",
        document_id="norm-1",
        temporal_status="event-date-active",
        relevance="high",
        confidence=0.9,
    )

    payload = block.to_dict()

    assert payload["full_citation"] == "Kanun m. 1"
    assert payload["short_quote"].startswith("Bu Kanun")
    assert payload["temporal_status"] == "event-date-active"


def test_evidence_block_rejects_missing_short_quote() -> None:
    with pytest.raises(ValueError, match="short_quote"):
        EvidenceBlock(
            claim="iddia",
            source_type="ictihat",
            citation_key="karar-1",
            full_citation="Yargıtay, 1. HD, E. 1, K. 2",
            short_quote="",
            source_url="",
            document_id="karar-1",
            temporal_status="unknown",
            relevance="medium",
            confidence=0.4,
        )


def test_source_scope_accepts_only_supported_values() -> None:
    for scope in ("targeted", "all", "selected"):
        assert validate_source_scope(scope) == scope

    with pytest.raises(ValueError, match="source_scope"):
        validate_source_scope("everything")


def test_undated_question_uses_current_law_baseline_and_missing_facts() -> None:
    context = TemporalLegalContext.from_question("Bir alacağımı nasıl tahsil ederim?")

    assert context.active_law_baseline == "current-law-assumption"
    assert context.assumptions
    assert "event_date" in context.missing_facts
    assert context.confidence < 1


def test_envelope_always_serializes_nonbinding_flags() -> None:
    envelope = LegalAnalysisEnvelope(
        analysis_only=False,
        non_binding=False,
        confidence=0.7,
        assumptions=["Tarih verilmedi."],
        missing_facts=["event_date"],
        evidence=[],
        source_scope="targeted",
    )

    payload = envelope.to_dict()

    assert payload["analysis_only"] is True
    assert payload["non_binding"] is True
    assert payload["source_scope"] == "targeted"

