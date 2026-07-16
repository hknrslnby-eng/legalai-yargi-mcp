"""Ortak, kaynaklı ve bağlayıcı olmayan analiz çıktı sözleşmeleri."""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from typing import Any, Literal


SourceScope = Literal["targeted", "all", "selected"]
_SOURCE_SCOPES = frozenset(("targeted", "all", "selected"))


def validate_source_scope(value: str) -> SourceScope:
    if value not in _SOURCE_SCOPES:
        raise ValueError("source_scope must be one of: targeted, all, selected")
    return value  # type: ignore[return-value]


def _serialize(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if is_dataclass(value):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


@dataclass
class EvidenceBlock:
    claim: str
    source_type: str
    citation_key: str
    full_citation: str
    short_quote: str
    source_url: str = ""
    document_id: str = ""
    temporal_status: str = "unknown"
    relevance: str = "medium"
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not self.short_quote.strip():
            raise ValueError("short_quote is required for every evidence block")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass
class LegalAnalysisEnvelope:
    """Her yüzeyde zorunlu olan araştırma taslağı/güvenlik zarfı."""

    analysis_only: bool = True
    non_binding: bool = True
    confidence: float = 0.0
    assumptions: list[str] | None = None
    missing_facts: list[str] | None = None
    evidence: list[EvidenceBlock] | None = None
    source_scope: SourceScope = "targeted"

    def __post_init__(self) -> None:
        # Bu iki bayrak çağıran tarafça kapatılamaz; sonuç hiçbir zaman
        # bağlayıcı görüş veya kesin hukukî sonuç olarak işaretlenmez.
        self.analysis_only = True
        self.non_binding = True
        validate_source_scope(self.source_scope)
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        self.assumptions = list(self.assumptions or [])
        self.missing_facts = list(self.missing_facts or [])
        self.evidence = list(self.evidence or [])

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)
