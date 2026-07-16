from datetime import date

import pytest

from legalai.packages.layers.temporal_context import (
    InvalEvent,
    LimitationAndPreclusionAnalyzer,
    NormRecord,
    TemporalLegalContextBuilder,
)
from legalai.packages.jurisdictions.base import JurisdictionProfile


class FakeTemporalBackend:
    def __init__(self, norms=None, events=None, fail=False):
        self.norms = norms or []
        self.events = events or []
        self.fail = fail

    async def search_norms(self, query, on_date, scope):
        if self.fail:
            raise RuntimeError("backend unavailable")
        return self.norms

    async def search_invalidation_events(self, query, date_from, date_to, scope):
        if self.fail:
            raise RuntimeError("backend unavailable")
        return self.events

    async def search_procedural_rules(self, query, scope):
        if self.fail:
            raise RuntimeError("backend unavailable")
        return []


@pytest.mark.asyncio
async def test_extracts_event_and_filing_dates_with_confidence() -> None:
    context = await TemporalLegalContextBuilder().build(
        "Olay tarihi 15.03.2020, dava tarihi 20.04.2024'tür."
    )

    assert context.event_dates[0].value == date(2020, 3, 15)
    assert context.filing_dates[0].value == date(2024, 4, 20)
    assert context.confidence > 0.5


@pytest.mark.asyncio
async def test_selects_active_norms_and_preserves_superseded_norms() -> None:
    backend = FakeTemporalBackend(
        norms=[
            NormRecord("old", "Eski norm", "m.1", date(2010, 1, 1), date(2021, 1, 1), "superseded", quote="old"),
            NormRecord("new", "Yeni norm", "m.1", date(2021, 1, 2), None, "active", quote="new"),
        ]
    )

    context = await TemporalLegalContextBuilder().build(
        "Olay tarihi 15.03.2020.", backend=backend
    )

    assert [norm.id for norm in context.applicable_norms] == ["old"]
    assert [norm.id for norm in context.superseded_norms] == ["new"]


@pytest.mark.asyncio
async def test_deferred_invalidation_is_not_applied_before_effective_date() -> None:
    backend = FakeTemporalBackend(
        events=[
            InvalEvent(
                "aym-1", "AYM", date(2024, 1, 1), date(2024, 2, 1), date(2024, 8, 1),
                "deferred-annulment", "m.1", "AYM E. 1 K. 2", quote="iptal"
            )
        ]
    )

    context = await TemporalLegalContextBuilder().build(
        "Olay tarihi 15.03.2024.", backend=backend
    )

    assert context.invalidation_events[0].effective_date == date(2024, 8, 1)
    assert "deferred" in context.invalidation_events[0].effect


def test_deadline_risks_are_conditional_and_include_missing_trigger_facts() -> None:
    profile = JurisdictionProfile(
        id="hukuk", name="Hukuk", procedural_deadlines={"dava": {"days": 30, "trigger": "tebliğ"}}
    )

    risks = LimitationAndPreclusionAnalyzer().analyze(
        question="Bir işleme karşı başvuru yapılabilir mi?",
        context=None,
        profile=profile,
    )

    assert risks[0].kind == "usulî_süre"
    assert risks[0].candidate_days == 30
    assert risks[0].missing_facts == ["tebliğ tarihi"]


@pytest.mark.asyncio
async def test_backend_failure_returns_uncertainty_not_fabricated_norm() -> None:
    context = await TemporalLegalContextBuilder().build(
        "Olay tarihi 15.03.2020.", backend=FakeTemporalBackend(fail=True)
    )

    assert context.applicable_norms == []
    assert context.missing_facts
    assert any("backend" in item for item in context.assumptions)
