import pytest

from legalai.packages.corpus.federated import (
    FederatedRetriever,
    SourceSearchResult,
)
from legalai.packages.layers.source_routing import SourceSubQuery, SourceQueryPlan


class _Adapter:
    def __init__(self, source_id, results=(), error=None):
        self.source_id = source_id
        self.results = list(results)
        self.error = error
        self.queries = []

    async def search(self, query, limit):
        self.queries.append(query)
        if self.error:
            raise self.error
        return self.results[:limit]


class _KeywordGate:
    def __init__(self, adapter):
        self.adapter = adapter
        self.source_id = adapter.source_id

    async def search(self, query, limit):
        raise AssertionError("planli arama legacy keyword gate'i kullanmamali")


@pytest.mark.asyncio
async def test_search_plan_bypasses_keyword_gate_and_preserves_duplicate_provenance():
    local = _Adapter("local_corpus", [SourceSearchResult("same", "Yerel", "local_corpus", "L")])
    live_adapter = _Adapter("rekabet_kurumu", [SourceSearchResult("same", "Canli", "rekabet_kurumu", "RK")])
    gated = _KeywordGate(live_adapter)
    retriever = FederatedRetriever(local=local, live=(gated,))
    plan = SourceQueryPlan((
        SourceSubQuery("local_corpus", "fiyat dagitim", "local", "corpus_only"),
        SourceSubQuery("rekabet_kurumu", "fiyat dagitim", "jurisdiction", "live_ready"),
    ))

    result = await retriever.search_plan(plan, limit=10)

    assert len(result.documents) == 1
    assert {item.source_id for item in result.documents[0].provenance} == {"local_corpus", "rekabet_kurumu"}
    assert result.availability == {"local_corpus": "available", "rekabet_kurumu": "available"}
    assert live_adapter.queries == ["fiyat dagitim"]


@pytest.mark.asyncio
async def test_search_plan_reports_unconfigured_and_skipped_sources():
    local = _Adapter("local_corpus")
    failing = _Adapter("danistay", error=TimeoutError("timeout"))
    retriever = FederatedRetriever(local=local, live=(failing,))
    plan = SourceQueryPlan(
        (SourceSubQuery("local_corpus", "soru", "local", "corpus_only"),
         SourceSubQuery("missing_source", "soru", "missing", "live_ready"),
         SourceSubQuery("danistay", "soru", "live", "live_ready")),
        (SourceSubQuery("bim", "soru", "pending", "verification_pending"),),
    )

    result = await retriever.search_plan(plan, limit=5)

    assert result.availability["missing_source"] == "unconfigured"
    assert result.availability["bim"] == "skipped:verification_pending"
    assert result.availability["danistay"] == "unavailable"
    assert {error.source_id for error in result.errors} == {"missing_source", "danistay"}
