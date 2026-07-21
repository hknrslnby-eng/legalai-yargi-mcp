import pytest

from legalai.packages.corpus.sources.official import ReklamKuruluOfficialAdapter
from legalai.packages.corpus.sources.registry import default_source_registry


@pytest.mark.asyncio
async def test_reklam_kurulu_adapter_normalizes_official_html_and_provenance():
    pages = {
        "https://ticaret.gov.tr/tuketici/ticari-reklamlar/reklam-kurulu-kararlari": '<a href="/karar/369-1">369 Sayılı Reklam Kurulu Kararı</a>',
        "https://ticaret.gov.tr/karar/369-1": "Kurul, reklamın tüketiciyi yanıltıcı nitelikte olduğuna karar verdi.",
    }

    async def fetch(url: str) -> str:
        return pages[url]

    results = await ReklamKuruluOfficialAdapter(fetch_text=fetch).search("reklam", 5)
    assert results[0].source_id == "reklam_kurulu"
    assert results[0].citation == "369 Sayılı Reklam Kurulu Kararı"
    assert results[0].source_url == "https://ticaret.gov.tr/karar/369-1"
    assert "yanıltıcı" in results[0].body
    assert results[0].metadata["retrieval_mode"] == "live"
    assert results[0].metadata["institution"] == "Reklam Kurulu"


def test_reklam_kurulu_is_registered_as_official_priority_source():
    descriptor = default_source_registry().get("reklam_kurulu")
    assert descriptor is not None
    assert descriptor.category == "official_institution"
    assert descriptor.priority < 60
