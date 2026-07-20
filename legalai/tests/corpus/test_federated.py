import asyncio

import pytest

from legalai.packages.corpus.federated import FederatedRetriever, SourceSearchResult


class FakeAdapter:
    def __init__(self, source_id, results=None, error=None, delay=0):
        self.source_id = source_id
        self.results = results or []
        self.error = error
        self.delay = delay
        self.started = False

    async def search(self, query, limit):
        self.started = True
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return self.results[:limit]


@pytest.mark.asyncio
async def test_federated_retriever_queries_local_and_live_in_parallel_and_preserves_provenance():
    local = FakeAdapter(
        "local",
        [SourceSearchResult(id="same", body="Yerel metin", source_id="local", citation="L")],
        delay=0.01,
    )
    live = FakeAdapter(
        "rekabet_kurumu",
        [SourceSearchResult(id="same", body="Resmi metin", source_id="rekabet_kurumu", citation="R")],
        delay=0.01,
    )

    result = await FederatedRetriever(local=local, live=(live,)).search("rekabet", limit=10)

    assert local.started and live.started
    assert len(result.documents) == 1
    assert result.documents[0].id == "same"
    assert {item.source_id for item in result.documents[0].provenance} == {"local", "rekabet_kurumu"}
    assert result.errors == []


@pytest.mark.asyncio
async def test_federated_retriever_isolates_source_failure_and_reports_availability():
    local = FakeAdapter("local", error=RuntimeError("local unavailable"))
    live = FakeAdapter(
        "hudoc",
        [SourceSearchResult(id="hudoc-1", body="HUDOC karar", source_id="hudoc", citation="HUDOC")],
    )

    result = await FederatedRetriever(local=local, live=(live,)).search("adil yargılanma", limit=10)

    assert [item.id for item in result.documents] == ["hudoc-1"]
    assert result.errors[0].source_id == "local"
    assert result.availability["local"] == "unavailable"
    assert result.availability["hudoc"] == "available"

