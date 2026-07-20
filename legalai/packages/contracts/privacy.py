from __future__ import annotations

import re

from .models import RedactionResult

_LABEL_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"(?im)^(?P<label>\s*(?:taraf(?:lar)?|party|parties|seller|buyer|lessor|lessee|contractor|employer|employee|unvan|yetkili)\s*:\s*)(?P<value>.+)$"
        ),
        "[TARAF_MASKELENDI]",
    ),
    (re.compile(r"(?im)^(?P<label>\s*(?:adres|address)\s*:\s*)(?P<value>.+)$"), "[ADRES_MASKELENDI]"),
    (re.compile(r"(?im)^(?P<label>\s*(?:imza|signature)\s*:\s*)(?P<value>.+)$"), "[IMZA_MASKELENDI]"),
    (re.compile(r"(?im)^(?P<label>\s*(?:e-?posta|email|e-mail)\s*:\s*)(?P<value>.+)$"), "[EPOSTA_MASKELENDI]"),
    (re.compile(r"(?im)^(?P<label>\s*(?:telefon|phone|gsm|mobile)\s*:\s*)(?P<value>.+)$"), "[TELEFON_MASKELENDI]"),
)

_UNLABELLED_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"(?im)^\s*(?:between|parties|taraflar)\s*[:\-]?\s*.+$"),
        "[TARAF_MASKELENDI]",
    ),
    (
        re.compile(
            r"(?im)^\s*.*(?:mah(?:allesi)?|sok(?:ak)?|cad(?:de)?|street|road|avenue|boulevard|blvd|rue|strasse|straße|via|calle|platz|postcode|postal\s+code).*$"
        ),
        "[ADRES_MASKELENDI]",
    ),
    (
        re.compile(r"(?im)^\s*(?:contact|attention|iletisim|iletişim)\s*[:\-]?\s*.+$"),
        "[ILETISIM_MASKELENDI]",
    ),
)

_STRUCTURED_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?<!\d)\d{11}(?!\d)"), "[TCKN_MASKELENDI]"),
    (re.compile(r"(?i)\b(?:vkn|vergi\s*no(?:su)?)\s*[:\-]?\s*\d{10}\b"), "[VKN_MASKELENDI]"),
    (re.compile(r"(?i)\bTR[0-9A-Z]{8,30}\b"), "[IBAN_MASKELENDI]"),
    (re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"), "[KART_MASKELENDI]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[EPOSTA_MASKELENDI]"),
    (
        re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3,4}\)?[\s-]?)\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"),
        "[TELEFON_MASKELENDI]",
    ),
)


def _replace_label(pattern: re.Pattern[str], replacement: str, text: str) -> str:
    return pattern.sub(lambda match: f"{match.group('label')}{replacement}", text)


class ContractPrivacyGate:
    """Redact contract identifiers in memory without a reversible map."""

    def redact(self, text: str) -> RedactionResult:
        redacted = text
        for pattern, replacement in _LABEL_RULES:
            redacted = _replace_label(pattern, replacement, redacted)
        for pattern, replacement in _UNLABELLED_RULES:
            redacted = pattern.sub(replacement, redacted)
        for pattern, replacement in _STRUCTURED_RULES:
            redacted = pattern.sub(replacement, redacted)
        return RedactionResult(text=redacted, persisted=False)
