from pathlib import Path

from pypdf import PdfWriter

from legalai.packages.bilirkisi.workflow import extract_report_text


def _blank_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with path.open("wb") as handle:
        writer.write(handle)


def test_scanned_pdf_uses_injected_local_ocr_provider(tmp_path: Path) -> None:
    path = tmp_path / "rapor.pdf"
    _blank_pdf(path)

    result = extract_report_text(
        file_path=path,
        ocr_provider=lambda _path: "Yangın yükü hesabı ve kalibrasyon kaydı.",
    )

    assert result.text.startswith("Yangın yükü")
    assert result.ocr_required is False
    assert result.warnings == ()


def test_scanned_pdf_exposes_ocr_requirement_when_no_provider_is_available(tmp_path: Path) -> None:
    path = tmp_path / "taranmis.pdf"
    _blank_pdf(path)

    result = extract_report_text(file_path=path, ocr_provider=lambda _path: None)

    assert result.text == ""
    assert result.ocr_required is True
    assert any("OCR" in warning for warning in result.warnings)
