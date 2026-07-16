import pytest

from legalai.packages.layers.opposing import run_opposing
from legalai.packages.shared.settings import settings
from legalai.packages.shared.types import Document


class FakeSourceBackend:
    async def search(self, query, limit):
        return []

    async def search_norms(self, query, on_date, scope):
        return []

    async def search_invalidation_events(self, query, date_from, date_to, scope):
        return []

    async def search_procedural_rules(self, query, scope):
        return []


@pytest.mark.asyncio
async def test_plaintiff_position_returns_counterarguments_and_rebutting_evidence() -> None:
    result = await run_opposing(
        question="Sözleşmeden doğan alacağımı nasıl tahsil ederim? Olay tarihi 15.03.2024.",
        position="Alacağım muaccel ve ödenmedi.",
        role="davacı",
        documents=[Document("d1", "Muacceliyet ve temerrüt değerlendirmesi.", "yargitay", "E. 1 K. 2")],
        temporal_backend=FakeSourceBackend(),
    )

    assert len(result.counter_arguments) == 5
    assert len(result.rebutting_evidence) <= 3
    assert result.temporal_context.event_dates
    assert result.strategy_options
    assert result.analysis_only is True
    assert result.non_binding is True

@pytest.mark.asyncio
async def test_host_mode_does_not_require_llm_and_preserves_missing_facts() -> None:
    result = await run_opposing(
        question="Bu uyuşmazlığı nasıl çözebilirim?",
        position="Haklı olduğumu düşünüyorum.",
        role="davacı",
        synthesize=False,
        document_backend=FakeSourceBackend(),
        temporal_backend=FakeSourceBackend(),
    )

    assert result.answer is None
    assert result.assistant_instructions
    assert result.missing_facts
    assert any("nonbinding" in result.assistant_instructions.lower() for _ in [0])


@pytest.mark.asyncio
async def test_feature_flag_disabled_returns_stable_disabled_result(monkeypatch) -> None:
    monkeypatch.setattr(settings, "enable_aggressive_opposing", False)

    result = await run_opposing("Soru", "Pozisyon", role="davacı")

    assert result.mode == "disabled"
    assert result.counter_arguments == []
    assert result.non_binding is True
