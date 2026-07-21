"""Shared local document intake primitives."""

from .intake import DocumentInput, ExtractedDocument, OcrProvider, extract_document

__all__ = ["DocumentInput", "ExtractedDocument", "OcrProvider", "extract_document"]
