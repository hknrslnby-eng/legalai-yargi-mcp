from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from pypdf import PdfWriter

from legalai.packages.contracts import ContractReviewRequest, extract_contract


def make_docx(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "contract.docx"
    document_xml = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
        f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>"
        "</w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
    return path


def make_scanned_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "scanned.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    with path.open("wb") as handle:
        writer.write(handle)
    return path


def test_contract_review_request_requires_exactly_one_contract_source(tmp_path):
    with pytest.raises(ValueError, match="exactly one"):
        ContractReviewRequest(
            contract_text=None,
            file_path=None,
            purpose="review",
            position="buyer",
            detail_level="standard",
            event_dates=None,
            jurisdiction_hint=None,
            server_side_synthesis=False,
        )

    with pytest.raises(ValueError, match="exactly one"):
        ContractReviewRequest(
            contract_text="MADDE 1 - Bedel",
            file_path=tmp_path / "contract.txt",
            purpose="review",
            position="buyer",
            detail_level="standard",
            event_dates=None,
            jurisdiction_hint=None,
            server_side_synthesis=False,
        )

    request = ContractReviewRequest(
        contract_text="MADDE 1 - Bedel",
        file_path=None,
        purpose="review",
        position="buyer",
        detail_level="standard",
        event_dates=["2026-07-20"],
        jurisdiction_hint="TR",
        server_side_synthesis=False,
    )

    assert request.contract_text == "MADDE 1 - Bedel"


def test_contract_intake_reads_docx_and_signals_scanned_pdf(tmp_path):
    docx_path = make_docx(tmp_path, "MADDE 1 - Bedel")

    intake = extract_contract(file_path=docx_path)

    assert intake.format == "docx"
    assert intake.clauses[0].number == "1"

    scanned = extract_contract(file_path=make_scanned_pdf(tmp_path))

    assert scanned.ocr_required is True


def test_extract_contract_reads_txt_and_md_from_local_files(tmp_path):
    txt_path = tmp_path / "contract.txt"
    txt_path.write_text("MADDE 1 - Teslim\nTeslim tarihi 20.07.2026.", encoding="utf-8")
    md_path = tmp_path / "contract.md"
    md_path.write_text("# ARTICLE 2 - Payment\nUSD 5000 shall be paid in London.", encoding="utf-8")

    txt_intake = extract_contract(file_path=txt_path)
    md_intake = extract_contract(file_path=md_path)

    assert txt_intake.format == "txt"
    assert "Teslim" in txt_intake.text
    assert md_intake.format == "md"
    assert "ARTICLE 2" in md_intake.text


def test_extract_contract_rejects_unsupported_extension(tmp_path):
    path = tmp_path / "contract.rtf"
    path.write_text("{\\rtf1}", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported"):
        extract_contract(file_path=path)


def test_extract_contract_rejects_missing_or_empty_input(tmp_path):
    with pytest.raises(ValueError, match="text or file_path"):
        extract_contract()

    with pytest.raises(ValueError, match="empty"):
        extract_contract(text="   ")

    empty_path = tmp_path / "empty.txt"
    empty_path.write_text("   ", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        extract_contract(file_path=empty_path)


def test_extract_contract_detects_foreign_language_and_foreign_elements():
    intake = extract_contract(
        text=(
            "ARTICLE 7 - Governing Law\n"
            "This agreement is governed by English law and disputes shall be resolved by arbitration in London. "
            "The fee is EUR 15,000."
        )
    )

    assert intake.language == "foreign"
    assert intake.foreign_element_signals
    assert any("governing" in signal.lower() or "arbitration" in signal.lower() for signal in intake.foreign_element_signals)
