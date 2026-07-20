import pytest

from legalai.packages.corpus.sources.official import OfficialHtmlCollectionAdapter


@pytest.mark.asyncio
async def test_official_html_collection_adapter_filters_query_and_preserves_urls():
    pages = {
        "https://example.test/kararlar": '<a href="/karar/1">Ayrımcılık kararı</a><a href="/karar/2">İhale kararı</a>',
        "https://example.test/karar/1": "Kurul kararının tam metni ve gerekçesi.",
    }

    async def fetch(url):
        return pages[url]

    adapter = OfficialHtmlCollectionAdapter(
        source_id="tihek",
        collection_urls=("https://example.test/kararlar",),
        fetch_text=fetch,
    )

    results = await adapter.search("ayrımcılık", 10)

    assert len(results) == 1
    assert results[0].source_id == "tihek"
    assert results[0].source_url == "https://example.test/karar/1"
    assert "tam metni" in results[0].body

