import pytest

from legalai.apps.api.routes import OpposingRequest
from legalai.packages.layers.opposing import run_opposing
from legalai.packages.shared.types import Document


class FakeSourceBackend:
    def __init__(self):
        self.queries = []

    async def search(self, query, limit):
        self.queries.append(query)
        return [Document("d2", "Karşıt içtihat alıntısı.", "danistay", "D. E. 3 K. 4")]

    async def search_norms(self, query, on_date, scope):
        return []

    async def search_invalidation_events(self, query, date_from, date_to, scope):
        return []

    async def search_procedural_rules(self, query, scope):
        return []


@pytest.mark.asyncio
async def test_week9_flow_preserves_structured_fields_without_server_llm():
    result = await run_opposing(
        question="Ödenmeyen alacağım için 15.03.2024 olay tarihinden sonra hangi yollar var?",
        position="Alacaklıyım ve ödeme yapılmadı.",
        role="davacı",
        documents=[Document("d1", "Muacceliyet ve temerrüt alıntısı.", "yargitay", "E. 1 K. 2")],
        synthesize=False,
        document_backend=FakeSourceBackend(),
        temporal_backend=FakeSourceBackend(),
    )
    payload = result.to_dict()

    assert payload["counter_arguments"]
    assert payload["temporal_context"]["event_dates"]
    assert payload["strategy_options"]
    assert payload["forum_candidates"]
    assert payload["evidence"]
    assert payload["analysis_only"] is True
    assert payload["non_binding"] is True


def test_opposing_request_restricts_roles_and_source_scope():
    request = OpposingRequest(
        question="soru",
        position="pozisyon",
        role="davacı",
        source_scope="selected",
        selected_source_ids=["d1"],
    )

    assert request.source_scope == "selected"
    assert request.selected_source_ids == ["d1"]


@pytest.mark.asyncio
async def test_single_legalai_flow_retrieves_question_and_counterargument_cases():
    backend = FakeSourceBackend()
    result = await run_opposing(
        question="Ödenmeyen alacağım için hangi yol var?",
        position="Alacaklıyım.",
        role="davacı",
        document_backend=backend,
        temporal_backend=backend,
    )

    assert result.rebutting_evidence
    assert backend.queries[0] == "Ödenmeyen alacağım için hangi yol var?"
    assert len(backend.queries) >= 4  # soru + en az üç karşı argüman araması
