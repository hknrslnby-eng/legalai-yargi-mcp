from datetime import date

import pytest

from legalai.packages.layers.legal_source_backend import IntegratedLegalSourceBackend
from legalai.packages.shared.types import Document


class FakeDecisionBackend:
    def __init__(self):
        self.queries = []

    async def search(self, query, limit):
        self.queries.append((query, limit))
        return [Document("d1", "İptal ve yürütmenin durdurulması değerlendirmesi.", "danistay", "D. E. 1 K. 2")]


class FakeNormClient:
    async def search_norm_denetimi_decisions(self, params):
        class Summary:
            decision_reference_no = "E. 2024/1, K. 2024/2"
            decision_page_url = "https://example.test/aym/1"
            decision_outcome_summary = "İptal istemi hakkında karar"
            decision_date_summary = "15.03.2024"

        class Result:
            decisions = [Summary()]

        return Result()

    async def get_decision_document_as_markdown(self, url):
        class Doc:
            official_gazette_info_from_page = "01.04.2024 / 32500"
            markdown_chunk = "İptal kararının gerekçesi."

        return Doc()


@pytest.mark.asyncio
async def test_integrated_backend_delegates_decision_search_and_normalizes_norm_event():
    decisions = FakeDecisionBackend()
    backend = IntegratedLegalSourceBackend(decision_backend=decisions, norm_client=FakeNormClient())

    documents = await backend.search_documents("sözleşme", 3)
    events = await backend.search_invalidation_events("sözleşme", date(2024, 1, 1), date(2024, 12, 31), "all")

    assert documents[0].id == "d1"
    assert decisions.queries == [("sözleşme", 3)]
    assert events[0].authority == "AYM"
    assert events[0].decision_date == date(2024, 3, 15)
    assert events[0].publication_date == date(2024, 4, 1)
    assert events[0].effective_date is None


@pytest.mark.asyncio
async def test_backend_returns_danistay_reference_without_inventing_date():
    backend = IntegratedLegalSourceBackend(decision_backend=FakeDecisionBackend(), norm_client=FakeNormClient())

    events = await backend.search_invalidation_events("iptal", None, None, "targeted")

    assert any(event.authority == "Danıştay" for event in events)
    danistay_event = next(event for event in events if event.authority == "Danıştay")
    assert danistay_event.decision_date is None
    assert danistay_event.effective_date is None
