"""Tarih, yürürlük ve süre risklerini kaynak backend'lerine bağlayan katman."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol

from legalai.packages.jurisdictions.base import JurisdictionProfile
from legalai.packages.shared.evidence import SourceScope, validate_source_scope
from legalai.packages.shared.temporal import DateObservation, TemporalLegalContext


@dataclass
class NormRecord:
    id: str
    title: str
    citation: str
    effective_from: date | None
    effective_to: date | None
    status: str
    source_url: str = ""
    quote: str = ""
    confidence: float = 0.0


@dataclass
class InvalEvent:
    id: str
    authority: str
    decision_date: date | None
    publication_date: date | None
    effective_date: date | None
    effect: str
    affected_norm: str
    citation: str
    source_url: str = ""
    quote: str = ""
    confidence: float = 0.0


@dataclass
class DeadlineRisk:
    kind: str
    trigger: str
    candidate_days: int | None
    missing_facts: list[str] = field(default_factory=list)
    interruption_or_suspension_facts: list[str] = field(default_factory=list)
    uncertainty: str = ""
    evidence: list[Any] = field(default_factory=list)


class TemporalSourceBackend(Protocol):
    async def search_norms(self, query: str, on_date: date, scope: SourceScope) -> list[NormRecord]: ...

    async def search_invalidation_events(
        self, query: str, date_from: date | None, date_to: date | None, scope: SourceScope
    ) -> list[InvalEvent]: ...

    async def search_procedural_rules(self, query: str, scope: SourceScope) -> list[NormRecord]: ...


_DATE_PATTERNS = (
    re.compile(r"(?P<day>\d{1,2})[./](?P<month>\d{1,2})[./](?P<year>\d{4})"),
    re.compile(r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"),
)


def _observations(question: str) -> list[DateObservation]:
    observations: list[DateObservation] = []
    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(question):
            try:
                value = date(
                    int(match.group("year")),
                    int(match.group("month")),
                    int(match.group("day")),
                )
            except ValueError:
                continue
            prefix = question[max(0, match.start() - 30) : match.start()].lower()
            if "dava" in prefix or "başvuru" in prefix:
                label = "filing_date"
            elif "tebliğ" in prefix or "bildirim" in prefix:
                label = "notice_date"
            else:
                label = "event_date"
            observations.append(DateObservation(label, value, "day", "explicit date in question", 0.95))
    return observations


class TemporalLegalContextBuilder:
    async def build(
        self,
        question: str,
        jurisdiction_hint: str | None = None,
        source_scope: SourceScope = "targeted",
        selected_source_ids: list[str] | None = None,
        backend: TemporalSourceBackend | None = None,
    ) -> TemporalLegalContext:
        del jurisdiction_hint
        validate_source_scope(source_scope)
        observations = _observations(question)
        if not observations:
            context = TemporalLegalContext.from_question(question)
            if source_scope == "selected" and not selected_source_ids:
                context.missing_facts.append("selected_source_ids")
            return context

        event_dates = [item for item in observations if item.label == "event_date"]
        filing_dates = [item for item in observations if item.label == "filing_date"]
        if not event_dates:
            event_dates = observations[:1]
        context = TemporalLegalContext(
            event_dates=event_dates,
            filing_dates=filing_dates,
            active_law_baseline="date-specific-pending-source-resolution",
            assumptions=["Tarih gözlemleri sorudaki açık tarihlerden çıkarıldı."],
            confidence=min(item.confidence for item in observations),
        )
        if source_scope == "selected" and not selected_source_ids:
            context.missing_facts.append("selected_source_ids")
        if backend is None:
            context.missing_facts.append("temporal_source_backend")
            context.assumptions.append("Mevzuat ve iptal olayları backend verilmediği için doğrulanmadı.")
            return context

        event_date = event_dates[0].value
        try:
            norms = await backend.search_norms(question, event_date, source_scope)
            context.applicable_norms = [
                norm for norm in norms if _active_on(norm, event_date)
            ]
            context.superseded_norms = [
                norm for norm in norms if not _active_on(norm, event_date)
            ]
            context.invalidation_events = await backend.search_invalidation_events(
                question, event_date, filing_dates[0].value if filing_dates else None, source_scope
            )
        except Exception as exc:
            context.missing_facts.append("temporal_source_results")
            context.assumptions.append(f"temporal backend unavailable: {type(exc).__name__}")
            context.confidence = min(context.confidence, 0.3)
        return context


def _active_on(norm: NormRecord, on_date: date) -> bool:
    if norm.effective_from and on_date < norm.effective_from:
        return False
    if norm.effective_to and on_date > norm.effective_to:
        return False
    return norm.status in {"active", "in-force", "yürürlükte"} or (
        norm.status == "superseded" and norm.effective_to is not None and on_date <= norm.effective_to
    )


class LimitationAndPreclusionAnalyzer:
    def analyze(
        self,
        question: str,
        context: TemporalLegalContext | None,
        profile: JurisdictionProfile,
    ) -> list[DeadlineRisk]:
        del question, context
        risks: list[DeadlineRisk] = []
        for label, raw_rule in profile.procedural_deadlines.items():
            rule = raw_rule if isinstance(raw_rule, dict) else {"days": raw_rule}
            trigger = str(rule.get("trigger", "başlangıç olayı"))
            days = rule.get("days")
            kind = str(rule.get("kind", "usulî_süre"))
            risks.append(
                DeadlineRisk(
                    kind=kind,
                    trigger=trigger,
                    candidate_days=int(days) if days is not None else None,
                    missing_facts=[f"{trigger} tarihi"],
                    uncertainty=f"{label} süresinin başlangıcı ve kesilme/durma halleri ayrıca doğrulanmalı.",
                )
            )
        return risks
