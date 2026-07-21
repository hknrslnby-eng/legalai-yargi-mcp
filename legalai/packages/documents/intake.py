from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from xml.etree import ElementTree


@dataclass(frozen=True)
class DocumentInput:
    text: str | None = None
    file_path: Path | None = None


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    format: str
    source_name: str
    ocr_required: bool = False
    warnings: tuple[str, ...] = ()


OcrProvider = Callable[[Path], str | None]
_TEXT_EXTENSIONS = {".txt", ".md"}
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def _docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    return "\n".join(
        (node.text or "").strip()
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1] == "t" and (node.text or "").strip()
    )


def _ocr(path: Path, provider: OcrProvider | None) -> tuple[str, bool, tuple[str, ...]]:
    if provider is None:
        return "", True, ("OCR gerekli: bir OCR sağlayıcısı sağlanmadı.",)
    text = provider(path) or ""
    if text.strip():
        return text, False, ()
    return "", True, ("OCR gerekli veya sonuç üretmedi; metin doğrulanamadı.",)


def extract_document(value: DocumentInput, ocr_provider: OcrProvider | None = None) -> ExtractedDocument:
    if (value.text is None) == (value.file_path is None):
        raise ValueError("Exactly one of text or file_path must be provided.")
    if value.text is not None:
        if not value.text.strip():
            raise ValueError("Document input is empty.")
        return ExtractedDocument(value.text, "text", "inline")

    path = Path(value.file_path)  # type: ignore[arg-type]
    if not path.is_file():
        raise FileNotFoundError(str(path))
    suffix = path.suffix.lower()
    fmt = suffix.lstrip(".")
    if suffix in _TEXT_EXTENSIONS:
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            raise ValueError("Document input is empty.")
        return ExtractedDocument(text, fmt, path.name)
    if suffix == ".docx":
        text = _docx_text(path)
        if not text.strip():
            raise ValueError("Document input is empty.")
        return ExtractedDocument(text, fmt, path.name)
    if suffix == ".pdf":
        from pypdf import PdfReader

        text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
        if text.strip():
            return ExtractedDocument(text, fmt, path.name)
        extracted, required, warnings = _ocr(path, ocr_provider)
        return ExtractedDocument(extracted, fmt, path.name, required, warnings)
    if suffix in _IMAGE_EXTENSIONS:
        extracted, required, warnings = _ocr(path, ocr_provider)
        return ExtractedDocument(extracted, fmt, path.name, required, warnings)
    raise ValueError(f"Unsupported document file extension: {suffix or 'none'}")
