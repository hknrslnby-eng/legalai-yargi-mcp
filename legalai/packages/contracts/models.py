from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
class ContractClassification:
    legal_nature: str
    classification_method: str
    foreign_law_layer: str
    confidence: float
    signals: tuple[str, ...] = ()
    tbk_19_warning: str = "Başlık yerine gerçek ortak irade ve edim dengesi değerlendirilmelidir."


@dataclass(frozen=True)
class PersonaRouteDecision:
    persona_id: str
    invoked: bool
    positive_triggers: tuple[str, ...] = ()
    negative_reason: str = ""
    priority: str = "supporting"
    confidence: float = 0.0
    verification_needed: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContractIssue:
    issue_id: str
    clause_number: str | None
    finding: str
    risk_level: str
    legal_rationale: str
    operational_rationale: str
    personas: tuple[str, ...]
    missing_facts: tuple[str, ...] = ()


@dataclass
class ContractReviewResult:
    executive_summary: str
    classification: dict[str, Any]
    persona_routes: list[dict[str, Any]]
    clause_findings: list[dict[str, Any]]
    gap_findings: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    temporal_context: Any
    operational_context: dict[str, Any]
    assistant_instructions: str
    privacy: dict[str, Any]
    analysis_only: bool = True
    non_binding: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "executive_summary": self.executive_summary,
            "classification": self.classification,
            "persona_routes": self.persona_routes,
            "clause_findings": self.clause_findings,
            "gap_findings": self.gap_findings,
            "evidence": self.evidence,
            "temporal_context": self.temporal_context,
            "operational_context": self.operational_context,
            "assistant_instructions": self.assistant_instructions,
            "privacy": self.privacy,
            "analysis_only": True,
            "non_binding": True,
        }


@dataclass(frozen=True)
class RedactionResult:
    text: str
    persisted: bool = False
