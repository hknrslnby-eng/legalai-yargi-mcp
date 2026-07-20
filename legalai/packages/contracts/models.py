from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ContractReviewRequest:
    contract_text: str | None
    file_path: Path | None
    purpose: str
    position: str
    detail_level: str
    event_dates: list[str] | None
    jurisdiction_hint: str | None
    server_side_synthesis: bool

    def __post_init__(self) -> None:
        has_text = self.contract_text is not None
        has_file = self.file_path is not None
        if has_text == has_file:
            raise ValueError("exactly one of contract_text and file_path is required.")


@dataclass(frozen=True)
class Clause:
    position: int
    number: str | None = None
    heading: str | None = None
    body: str = ""


@dataclass(frozen=True)
class ContractIntake:
    text: str
    format: str
    clauses: tuple[Clause, ...]
    language: str
    foreign_element_signals: tuple[str, ...]
    ocr_required: bool = False


@dataclass(frozen=True)
class RedactionResult:
    text: str
    persisted: bool = False
