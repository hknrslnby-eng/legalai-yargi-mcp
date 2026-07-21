import pytest

from legalai.packages.corpus.sources.international import (
    CompetitionReportAdapter,
    CuriaOfficialAdapter,
    DgCompOfficialAdapter,
    OecdCompetitionAdapter,
    OfficialCollectionAdapter,
)


@pytest.mark.asyncio
async def test_official_collection_adapter_preserves_authority_and_license_metadata():
    pages = {
        "https://source.test/collection": '<a href="/decision-1">Market report</a>',
        "https://source.test/decision-1": '<main>Official market report body.</main>',
    }

    async def fetch_text(url: str) -> str:
        return pages[url]

    adapter = OfficialCollectionAdapter(
        source_id="competition_reports",
        collection_urls=("https://source.test/collection",),
        source_kind="economic_report",
        authority_level="non_binding_economic_reference",
        license_note="Atıf gerekli.",
        fetch_text=fetch_text,
    )

    results = await adapter.search("market report", 5)

    assert len(results) == 1
    assert results[0].metadata["authority_level"] == "non_binding_economic_reference"
    assert results[0].metadata["source_kind"] == "economic_report"
    assert results[0].metadata["license_note"] == "Atıf gerekli."
    assert results[0].metadata["retrieval_mode"] == "live"


@pytest.mark.asyncio
async def test_official_collection_adapter_surfaces_fetch_error():
    async def fetch_text(url: str) -> str:
        raise RuntimeError("source unavailable")

    adapter = OfficialCollectionAdapter(
        source_id="dg_comp",
        collection_urls=("https://source.test/collection",),
        source_kind="foreign_institution_decision",
        authority_level="comparative_institution_reference",
        fetch_text=fetch_text,
    )

    with pytest.raises(RuntimeError, match="source unavailable"):
        await adapter.search("competition", 5)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("factory", "source_id", "document_type"),
    [
        (DgCompOfficialAdapter, "dg_comp", "official_document"),
        (CuriaOfficialAdapter, "curia", "judicial_decision"),
        (OecdCompetitionAdapter, "oecd_competition", "policy_report"),
        (CompetitionReportAdapter, "competition_reports", "market_report"),
    ],
)
async def test_concrete_international_adapters_keep_source_identity(factory, source_id, document_type):
    pages = {
        "https://source.test/collection": '<a href="/decision-1">Competition item</a>',
        "https://source.test/decision-1": '<main>Source body.</main>',
    }

    async def fetch_text(url: str) -> str:
        return pages[url]

    adapter = factory(fetch_text=fetch_text)
    adapter.collection_urls = ("https://source.test/collection",)

    results = await adapter.search("competition", 1)

    assert results[0].source_id == source_id
    assert results[0].metadata["document_type"] == document_type
    assert results[0].metadata["authority_level"]


@pytest.mark.asyncio
async def test_official_collection_adapter_limit_zero_returns_no_documents():
    async def fetch_text(url: str) -> str:
        raise AssertionError("fetch must not run for limit zero")

    adapter = OfficialCollectionAdapter(
        source_id="dg_comp",
        collection_urls=("https://source.test/collection",),
        source_kind="foreign_institution_decision",
        authority_level="comparative_institution_reference",
        fetch_text=fetch_text,
    )

    assert await adapter.search("competition", 0) == []
