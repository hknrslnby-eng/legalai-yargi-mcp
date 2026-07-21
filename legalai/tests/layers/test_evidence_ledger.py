from legalai.packages.layers.evidence_ledger import (
    build_evidence_ledger,
    validate_evidence_ledger,
)
from legalai.packages.shared.types import Document


def test_build_evidence_ledger_preserves_supported_sources_and_metadata():
    records = build_evidence_ledger(
        claims=[
            {
                "id": "claim-iban",
                "text": "Transferin belirli IBAN'a yapıldığı ileri sürülüyor.",
                "source_ids": ["doc-iban"],
                "relevance": "high",
                "temporal_note": "Transfer tarihi ayrıca doğrulanmalı.",
            },
            {
                "id": "claim-ratio",
                "text": "Mahkeme teknik raporu karar gerekçesinde benimsedi.",
                "source_ids": ["doc-ratio"],
                "relevance": "medium",
            },
        ],
        documents=[
            Document(
                id="doc-iban",
                source="bank_record",
                citation="Banka dekontu, 12.06.2025 tarihli transfer kaydı",
                body="12.06.2025 tarihinde TR00 0000 0000 0000 0000 0000 00 IBAN hesabına 50.000 TL gönderildi.",
                metadata={"page": "1", "paragraph": "2", "authority_level": "primary"},
            ),
            Document(
                id="doc-ratio",
                source="court_decision",
                citation="Yargıtay 1. HD 2025/10 E., 2025/20 K.",
                body="Mahkeme, bilirkişi teknik raporunu esas alarak sistem kayıtlarının tutarlı olduğuna değinmiştir.",
                metadata={"page": "4", "authority_level": "high"},
            ),
        ],
        source_evidence=(
            {
                "claim_id": "claim-ratio",
                "source_id": "doc-ratio",
                "ratio_or_dictum": "ratio",
                "pin": "s.4",
                "relevance": "high",
            },
        ),
    )

    assert [record.claim_id for record in records] == ["claim-iban", "claim-ratio"]
    assert all(record.analysis_only is True for record in records)
    assert all(record.non_binding is True for record in records)

    iban = records[0]
    assert iban.source_id == "doc-iban"
    assert iban.source_type == "bank_record"
    assert iban.full_citation == "Banka dekontu, 12.06.2025 tarihli transfer kaydı"
    assert "IBAN" in iban.short_quote
    assert iban.page == "1"
    assert iban.paragraph == "2"
    assert iban.authority_level == "primary"
    assert iban.temporal_note == "Transfer tarihi ayrıca doğrulanmalı."

    ratio = records[1]
    assert ratio.pin == "s.4"
    assert ratio.page == "4"
    assert ratio.ratio_or_dictum == "ratio"
    assert ratio.relevance == "high"


def test_validate_evidence_ledger_detects_unsupported_citations_and_empty_source_bodies():
    records = build_evidence_ledger(
        claims=[
            {
                "id": "claim-ghost",
                "text": "Desteksiz bir kaynak iddiası var.",
                "source_ids": ["ghost-1"],
            },
            {
                "id": "claim-empty",
                "text": "Boş gövdeli belge kısa alıntı üretememeli.",
                "source_ids": ["doc-empty"],
            },
        ],
        documents=[
            Document(
                id="doc-empty",
                source="technical_report",
                citation="Boş içerikli teknik ek",
                body="",
                metadata={"page": "7", "authority_level": "medium"},
            )
        ],
    )

    assert [record.source_id for record in records] == ["ghost-1", "doc-empty"]
    assert records[0].supported is False
    assert records[0].short_quote == ""
    assert records[1].short_quote == ""

    report = validate_evidence_ledger(records)

    assert report["analysis_only"] is True
    assert report["non_binding"] is True
    assert report["valid"] is False
    assert report["unsupported_citations"] == ["ghost-1"]
    assert report["empty_quote_source_ids"] == ["doc-empty"]
