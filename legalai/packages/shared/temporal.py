"""Tarih bilgisi eksik veya kısmi hukuk soruları için ortak bağlam tipleri."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal


DatePrecision = Literal["day", "month", "year", "unknown"]


@dataclass
class DateObservation:
    label: str
    value: date | None
    precision: DatePrecision
    basis: str
    confidence: float


@dataclass
class TemporalLegalContext:
    event_dates: list[DateObservation] = field(default_factory=list)
    filing_dates: list[DateObservation] = field(default_factory=list)
    reference_dates: list[DateObservation] = field(default_factory=list)
    active_law_baseline: str = "current-law-assumption"
    applicable_norms: list[Any] = field(default_factory=list)
    superseded_norms: list[Any] = field(default_factory=list)
    unresolved_norms: list[Any] = field(default_factory=list)
    invalidation_events: list[Any] = field(default_factory=list)
    deadline_risks: list[Any] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    missing_facts: list[str] = field(default_factory=list)
    confidence: float = 0.0

    @classmethod
    def from_question(cls, question: str) -> "TemporalLegalContext":
        """Tarih algılanmayan soruyu güncel hukuk varsayımıyla işaretler."""
        del question  # Tarih çıkarımı daha ileri temporal katmanda yapılır.
        return cls(
            assumptions=[
                "Olay ve dava tarihleri verilmediği için güncel hukuk başlangıç varsayımı kullanıldı."
            ],
            missing_facts=["event_date", "filing_date"],
            confidence=0.35,
        )
