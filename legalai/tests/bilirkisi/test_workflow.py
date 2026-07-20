from __future__ import annotations

import zipfile

import pytest

from legalai.packages.bilirkisi.workflow import (
    analyze_report,
    build_petition_draft,
    extract_report_text,
)


def test_extract_report_text_accepts_plain_text_and_masks_pii_for_external_prompt():
    result = extract_report_text(text="Teknik bulgu: ölçüm 17.4. TCKN 12345678901.")

    assert result.text.startswith("Teknik bulgu")
    assert result.external_text != result.text
    assert "12345678901" not in result.external_text
    assert result.format == "text"


def test_extract_report_text_reads_docx_without_sending_original_file(tmp_path):
    path = tmp_path / "rapor.docx"
    document_xml = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
        "<w:body><w:p><w:r><w:t>Teknik değerlendirme ve sonuç.</w:t></w:r></w:p></w:body>"
        "</w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)

    result = extract_report_text(file_path=path)

    assert result.format == "docx"
    assert "Teknik değerlendirme" in result.text


def test_extract_report_text_uses_injected_ocr_provider_for_image_reports(tmp_path):
    path = tmp_path / "rapor.png"
    path.write_bytes(b"not-a-real-image-for-injected-provider")

    result = extract_report_text(file_path=path, ocr_provider=lambda _: "Görüntüde teknik bulgu vardır.")

    assert result.format == "png"
    assert result.ocr_required is False
    assert "teknik bulgu" in result.text


def test_extract_report_text_reports_ocr_requirement_when_no_engine_is_available(tmp_path):
    path = tmp_path / "rapor.jpg"
    path.write_bytes(b"not-a-real-image")

    result = extract_report_text(file_path=path, ocr_provider=lambda _: None)

    assert result.ocr_required is True
    assert result.warnings


@pytest.mark.asyncio
async def test_analysis_builds_technical_counterarguments_and_legal_grounding():
    result = await analyze_report(
        text="Bilirkişi, cihaz kalibrasyonunu incelemeden ölçümün kesin olduğunu kabul etmiştir.",
        question="Bu rapora itiraz için hukuki ve teknik analiz yap.",
        technical_domain="mühendislik",
        event_dates=["01.02.2024"],
        case_date="15.03.2024",
    )

    assert result.production_enabled is True
    assert result.claims
    assert result.claims[0].technical_counterargument
    assert result.claims[0].legal_links
    assert result.temporal_context["event_dates"] == ["01.02.2024"]
    assert result.non_binding is True


def test_petition_draft_maps_each_report_claim_to_objection_and_missing_evidence():
    analysis = analyze_report_sync_for_test()

    draft = build_petition_draft(analysis, court="Görevli mahkeme")

    assert "Bilirkişi raporuna itiraz" in draft.title
    assert len(draft.objections) == len(analysis.claims)
    assert draft.objections[0].technical_basis
    assert draft.objections[0].legal_basis
    assert draft.missing_evidence
    assert draft.non_binding is True


def analyze_report_sync_for_test():
    import asyncio

    return asyncio.run(
        analyze_report(
            text="Rapor, numune alma yöntemini açıklamadan sonuca ulaşmıştır.",
            question="İtiraz dilekçesi hazırla.",
            technical_domain="laboratuvar",
        )
    )
