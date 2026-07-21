from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

PetitionOperation = Literal["draft", "review", "shorten", "lengthen"]


@dataclass(frozen=True)
class PetitionRequest:
    operation: PetitionOperation
    petition_text: str | None
    question: str = ""
    party_position: str = ""
    jurisdiction_hint: str | None = None
    event_dates: list[str] | None = None
    source_documents: list[dict[str, Any]] = field(default_factory=list)
    detail_level: str = "standard"


@dataclass
class PetitionResult:
    operation: PetitionOperation
    executive_summary: str
    sections: list[dict[str, Any]] = field(default_factory=list)
    paragraphs: list[dict[str, Any]] = field(default_factory=list)
    changes: list[dict[str, Any]] = field(default_factory=list)
    protected_topics: set[str] = field(default_factory=set)
    shortening_safeguards: dict[str, Any] = field(default_factory=dict)
    lengthening_safeguards: dict[str, Any] = field(default_factory=dict)
    quality: dict[str, Any] = field(default_factory=dict)
    source_requirements: dict[str, Any] = field(default_factory=dict)
    evidence_ledger: list[dict[str, Any]] = field(default_factory=list)
    operational_cards: list[dict[str, Any]] = field(default_factory=list)
    cross_domain_inquiry: dict[str, Any] = field(default_factory=dict)
    operational_context: dict[str, Any] = field(default_factory=dict)
    temporal_context: dict[str, Any] = field(default_factory=dict)
    missing_facts: list[str] = field(default_factory=list)
    analysis_only: bool = True
    non_binding: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = self.__dict__.copy()
        payload["protected_topics"] = sorted(self.protected_topics)
        payload["analysis_only"] = True
        payload["non_binding"] = True
        return payload
