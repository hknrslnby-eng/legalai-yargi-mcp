"""run_deep_research'ün iki modunu da (host_orchestrated / server_synthesized)
gerçek ağ/LLM çağrısı yapmadan doğrular — LLMRouter ve run_pipeline enjekte/
monkeypatch edilir."""
import pytest

import legalai.packages.layers.deep_research as deep_research
from legalai.packages.layers.deep_research import (
    SubResearch,
    run_deep_research,
    suggest_subquestions_from_axes,
)
from legalai.packages.llm.router import LLMNotConfiguredError


class _FakeRouter:
    """`route()` çağrılarını sırayla scriptlenen cevaplarla karşılar."""

    def __init__(self, scripted_answers, configured=True):
        self._scripted_answers = list(scripted_answers)
        self._configured = configured
        self.calls = []

    def route(self, task="simple"):
        if not self._configured:
            raise LLMNotConfiguredError("anahtar yok")
        return self

    async def generate(self, system, user):
        self.calls.append({"system": system, "user": user})
        return self._scripted_answers.pop(0)


def test_suggest_subquestions_from_axes_uses_jurisdiction_profile():
    subquestions = suggest_subquestions_from_axes("zarar davası", "hukuk", depth=2)

    assert len(subquestions) == 2
    assert all("zarar davası" in q for q in subquestions)


def test_suggest_subquestions_from_axes_falls_back_to_question_without_axes():
    assert suggest_subquestions_from_axes("soru", None, depth=3) == ["soru"]


@pytest.mark.asyncio
async def test_run_deep_research_host_orchestrated_when_no_key(monkeypatch):
    monkeypatch.setattr(
        deep_research, "llm_router", _FakeRouter(scripted_answers=[], configured=False)
    )

    result = await run_deep_research("İşyerinde mobbing tazminatı nasıl hesaplanır?", depth=3, synthesize=False)

    assert result.mode == "host_orchestrated"
    assert result.answer is None
    assert result.citations == []
    assert result.instructions is not None
    assert "katmanli_analiz" in result.instructions
    assert result.subquestions


@pytest.mark.asyncio
async def test_run_deep_research_auto_detects_host_orchestrated_without_key(monkeypatch):
    monkeypatch.setattr(
        deep_research, "llm_router", _FakeRouter(scripted_answers=[], configured=False)
    )

    result = await run_deep_research("soru", synthesize=None)

    assert result.mode == "host_orchestrated"


@pytest.mark.asyncio
async def test_run_deep_research_server_synthesized_runs_planner_researcher_editor(monkeypatch):
    fake_router = _FakeRouter(
        scripted_answers=[
            '["alt soru 1", "alt soru 2"]',  # planner
            "[]",  # critic: yeterli, ek soru yok
            "Sentez cevap [#sub-d1] [#sub-d2].",  # editor
        ]
    )
    monkeypatch.setattr(deep_research, "llm_router", fake_router)

    async def _fake_research_subquestion(subquestion):
        doc_id = "sub-d1" if "1" in subquestion else "sub-d2"
        return SubResearch(
            subquestion=subquestion,
            answer=f"cevap [#{doc_id}]",
            citations=[doc_id],
            sources=[{"doc_id": doc_id, "citation": "c", "source": "yargitay"}],
        )

    monkeypatch.setattr(deep_research, "_research_subquestion", _fake_research_subquestion)

    result = await run_deep_research("soru", depth=2, synthesize=True)

    assert result.mode == "server_synthesized"
    assert result.subquestions == ["alt soru 1", "alt soru 2"]
    assert len(result.sub_results) == 2
    assert result.answer == "Sentez cevap [#sub-d1] [#sub-d2]."
    assert set(result.citations) == {"sub-d1", "sub-d2"}


@pytest.mark.asyncio
async def test_run_deep_research_retries_editor_on_hallucinated_citation(monkeypatch):
    fake_router = _FakeRouter(
        scripted_answers=[
            '["alt soru 1"]',  # planner
            "[]",  # critic
            "Uydurma [#hayali].",  # editor (ilk deneme)
            "Düzeltildi [#sub-d1].",  # editor (retry)
        ]
    )
    monkeypatch.setattr(deep_research, "llm_router", fake_router)

    async def _fake_research_subquestion(subquestion):
        return SubResearch(
            subquestion=subquestion,
            answer="cevap [#sub-d1]",
            citations=["sub-d1"],
            sources=[],
        )

    monkeypatch.setattr(deep_research, "_research_subquestion", _fake_research_subquestion)

    result = await run_deep_research("soru", depth=1, synthesize=True)

    assert result.answer == "Düzeltildi [#sub-d1]."
    assert result.citations == ["sub-d1"]


@pytest.mark.asyncio
async def test_run_deep_research_critic_triggers_extra_subquestion(monkeypatch):
    fake_router = _FakeRouter(
        scripted_answers=[
            '["alt soru 1"]',  # planner
            '["ek alt soru"]',  # critic: bir eksik var
            "Sentez [#sub-d1] [#extra-d1].",  # editor
        ]
    )
    monkeypatch.setattr(deep_research, "llm_router", fake_router)

    async def _fake_research_subquestion(subquestion):
        doc_id = "extra-d1" if "ek" in subquestion else "sub-d1"
        return SubResearch(subquestion=subquestion, answer=f"cevap [#{doc_id}]", citations=[doc_id])

    monkeypatch.setattr(deep_research, "_research_subquestion", _fake_research_subquestion)

    result = await run_deep_research("soru", depth=1, synthesize=True)

    assert result.subquestions == ["alt soru 1", "ek alt soru"]
    assert len(result.sub_results) == 2
