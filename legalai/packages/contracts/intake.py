from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from .models import Clause, ContractIntake

_SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}
_CLAUSE_PATTERN = re.compile(
    r"^(?:#+\s*)?(?:(?:madde|article|clause)\s+)?(?P<number>\d+(?:\.\d+)*)\s*(?:[-–—:.]\s*(?P<heading>.+))?$",
    re.IGNORECASE,
)


def _xml_text(xml: bytes) -> str:
    root = ElementTree.fromstring(xml)
    values = [node.text or "" for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "t"]
    return "\n".join(value.strip() for value in values if value.strip())


def _read_file(path: Path) -> tuple[str, str, bool]:
    suffix = path.suffix.lower()
    if suffix not in _SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported contract file extension: {suffix or 'none'}")
    if not path.is_file():
        raise FileNotFoundError(str(path))

    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace"), suffix.lstrip("."), False
    if suffix == ".docx":
        with zipfile.ZipFile(path) as archive:
            return _xml_text(archive.read("word/document.xml")), "docx", False

    from pypdf import PdfReader

    reader = PdfReader(str(path))
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    return extracted, "pdf", not extracted.strip()


def _detect_language(text: str) -> str:
    lowered = f" {text.casefold()} "
    turkish_score = sum(
        marker in lowered
        for marker in (" madde ", " sözleşme ", " taraf ", " teslim ", " ödeme ", " bedel ", " tarihi ", " türk ")
    ) + sum(character in text for character in "çğıöşüÇĞİÖŞÜ")
    foreign_score = sum(
        marker in lowered
        for marker in (" article ", " agreement ", " governed by ", " arbitration ", " shall ", " payment ", " english law ", " london ")
    )
    if turkish_score and foreign_score:
        return "mixed"
    if foreign_score:
        return "foreign"
    return "tr"


def _foreign_element_signals(text: str, language: str) -> tuple[str, ...]:
    lowered = text.casefold()
    signals: list[str] = []

    if language in {"foreign", "mixed"}:
        signals.append(f"Language signal: {language}")
    if re.search(r"\b(?:USD|EUR|GBP|CHF)\b|[$€£]", text):
        signals.append("Foreign currency reference detected.")
    if any(token in lowered for token in ("london", "england", "english law", "united kingdom", "germany", "paris", "new york")):
        signals.append("Foreign country or address reference detected.")
    if "governed by" in lowered or "governing law" in lowered or "english law" in lowered:
        signals.append("Governing law points to a foreign legal system.")
    if any(token in lowered for token in ("arbitration", "icc", "lcia", "siac")):
        signals.append("Arbitration forum suggests a foreign element.")
    if any(token in lowered for token in ("outside turkey", "abroad", "overseas", "delivery in london", "performed in london")):
        signals.append("Performance appears tied to a foreign location.")

    return tuple(dict.fromkeys(signals))


def _extract_clauses(text: str) -> tuple[Clause, ...]:
    lines = text.splitlines()
    clauses: list[Clause] = []
    current: Clause | None = None
    body_lines: list[str] = []

    def flush_current() -> None:
        nonlocal current, body_lines
        if current is None:
            return
        clauses.append(
            Clause(
                position=current.position,
                number=current.number,
                heading=current.heading,
                body="\n".join(line for line in body_lines if line).strip(),
            )
        )
        current = None
        body_lines = []

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            if body_lines and body_lines[-1] != "":
                body_lines.append("")
            continue

        normalized = re.sub(r"^#+\s*", "", line)
        match = _CLAUSE_PATTERN.match(normalized)
        starts_with_keyword = normalized.casefold().startswith(("madde ", "article ", "clause "))
        if match and (starts_with_keyword or match.group("heading")):
            flush_current()
            current = Clause(
                position=line_number,
                number=match.group("number"),
                heading=(match.group("heading") or "").strip() or None,
                body="",
            )
            continue

        if current is None:
            current = Clause(position=1, body="")
        body_lines.append(line)

    flush_current()
    if clauses:
        return tuple(clauses)
    stripped = text.strip()
    return (Clause(position=1, body=stripped),) if stripped else ()


def extract_contract(*, text: str | None = None, file_path: Path | None = None) -> ContractIntake:
    if (text is None) == (file_path is None):
        raise ValueError("Exactly one of text or file_path must be provided.")

    if text is not None:
        raw_text = text
        fmt = "text"
        ocr_required = False
    else:
        raw_text, fmt, ocr_required = _read_file(Path(file_path))

    if not raw_text or not raw_text.strip():
        if ocr_required:
            return ContractIntake(
                text="",
                format=fmt,
                clauses=(),
                language="tr",
                foreign_element_signals=(),
                ocr_required=True,
            )
        raise ValueError("Contract input is empty.")

    normalized = raw_text.strip()
    language = _detect_language(normalized)
    return ContractIntake(
        text=normalized,
        format=fmt,
        clauses=_extract_clauses(normalized),
        language=language,
        foreign_element_signals=_foreign_element_signals(normalized, language),
        ocr_required=ocr_required,
    )
