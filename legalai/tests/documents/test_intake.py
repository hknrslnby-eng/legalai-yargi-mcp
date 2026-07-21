from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from legalai.packages.documents.intake import DocumentInput, extract_document


def make_docx(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "document.docx"
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


def make_digital_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "digital.pdf"
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 72 720 Td (Shared intake text) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    with path.open("wb") as handle:
        writer.write(handle)
    return path


def test_document_input_requires_exactly_one_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Exactly one"):
        extract_document(DocumentInput())

    with pytest.raises(ValueError, match="Exactly one"):
        extract_document(DocumentInput(text="inline", file_path=tmp_path / "contract.txt"))


def test_extract_document_reads_inline_text_and_txt(tmp_path: Path) -> None:
    txt_path = tmp_path / "document.txt"
    txt_path.write_text("Satır 1\nSatır 2", encoding="utf-8")

    inline = extract_document(DocumentInput(text="Merhaba dünya"))
    txt_file = extract_document(DocumentInput(file_path=txt_path))

    assert inline.format == "text"
    assert inline.source_name == "inline"
    assert inline.text == "Merhaba dünya"
    assert txt_file.format == "txt"
    assert txt_file.text == "Satır 1\nSatır 2"


def test_extract_document_reads_docx_and_digital_pdf(tmp_path: Path) -> None:
    docx = extract_document(DocumentInput(file_path=make_docx(tmp_path, "Belge metni")))
    pdf = extract_document(DocumentInput(file_path=make_digital_pdf(tmp_path)))

    assert docx.format == "docx"
    assert docx.text == "Belge metni"
    assert pdf.format == "pdf"
    assert pdf.ocr_required is False
    assert "Shared intake text" in pdf.text


def test_extract_document_uses_injected_ocr_for_images_and_tiff(tmp_path: Path) -> None:
    png_path = tmp_path / "scan.png"
    png_path.write_bytes(b"fake-image")
    tif_path = tmp_path / "scan.tif"
    tif_path.write_bytes(b"fake-tif")
    tiff_path = tmp_path / "SCAN.TIFF"
    tiff_path.write_bytes(b"fake-tiff")

    provider = lambda path: f"OCR::{path.suffix.lower()}"

    png = extract_document(DocumentInput(file_path=png_path), ocr_provider=provider)
    tif = extract_document(DocumentInput(file_path=tif_path), ocr_provider=provider)
    tiff = extract_document(DocumentInput(file_path=tiff_path), ocr_provider=provider)

    assert png.text == "OCR::.png"
    assert png.ocr_required is False
    assert tif.text == "OCR::.tif"
    assert tif.format == "tif"
    assert tiff.text == "OCR::.tiff"
    assert tiff.format == "tiff"


def test_extract_document_reports_ocr_requirement_without_engine(tmp_path: Path) -> None:
    image_path = tmp_path / "scan.jpg"
    image_path.write_bytes(b"fake-image")
    scanned_pdf = make_scanned_pdf(tmp_path)

    image = extract_document(DocumentInput(file_path=image_path), ocr_provider=lambda _: None)
    pdf = extract_document(DocumentInput(file_path=scanned_pdf), ocr_provider=lambda _: None)

    assert image.text == ""
    assert image.ocr_required is True
    assert any("OCR" in warning for warning in image.warnings)
    assert pdf.text == ""
    assert pdf.ocr_required is True
    assert any("OCR" in warning for warning in pdf.warnings)
