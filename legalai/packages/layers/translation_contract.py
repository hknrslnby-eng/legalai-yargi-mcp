"""Model-neutral multilingual legal-output contract."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal


SUPPORTED_OUTPUT_LANGUAGES = ("tr", "en", "fr", "de", "ru", "ar", "es", "zh")
TranslationDirection = Literal["source_to_output", "output_to_source", "between_outputs"]


@dataclass(frozen=True)
class TranslationRequest:
    source_language: str
    output_language: str
    direction: TranslationDirection
    terminology_profile: str = "legal_default"
    preserve_citations: bool = True

    def __post_init__(self) -> None:
        if self.source_language not in SUPPORTED_OUTPUT_LANGUAGES:
            raise ValueError(f"Desteklenmeyen kaynak dili: {self.source_language}")
        if self.output_language not in SUPPORTED_OUTPUT_LANGUAGES:
            raise ValueError(f"Desteklenmeyen çıktı dili: {self.output_language}")
        if self.direction not in {"source_to_output", "output_to_source", "between_outputs"}:
            raise ValueError("Geçersiz translation direction")


# CELEX identifiers use a sector digit, four-digit year, document-type letter,
# and four-digit sequence (for example: CELEX:32016R0679).
_IMMUTABLE_ID = re.compile(
    r"\b(?:ECLI:[A-Z]{2}:[A-Z0-9.:-]+|CELEX:\d{5}[A-Z]\d{4}|"
    r"[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜ ]+\s+\d{4}/\d+\s*[EK]\.)\b"
)


def extract_immutable_citation_ids(text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(match.group(0).strip() for match in _IMMUTABLE_ID.finditer(text)))


def build_translation_instructions(request: TranslationRequest, text: str = "") -> str:
    ids = extract_immutable_citation_ids(text)
    citations = ", ".join(ids) if ids else "(metinde sabit kimlik bulunamadı)"
    return (
        f"Çıktı dili: {request.output_language}; kaynak dili: {request.source_language}; yön: {request.direction}. "
        f"Hukuk terminolojisi profili: {request.terminology_profile}. "
        "Yalnızca hukuki düzyazıyı çevir; resmi kurum/mahkeme adlarını, kaynak provenance'ını, norm ve karar kimliklerini değiştirme. "
        f"Sabit tutulacak kimlikler: {citations}. "
        "Çıktıyı yeminli/sertifikalı çeviri veya resmi tercüme olarak sunma; terminolojik eşdeğerlik ve belirsizlikleri belirt. "
        f"Atıfları koru: {request.preserve_citations}. Çıktı analysis-only ve non-binding'dir."
    )
