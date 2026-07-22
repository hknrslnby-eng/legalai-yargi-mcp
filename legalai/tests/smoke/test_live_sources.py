import os

import pytest

from legalai.packages.corpus.sources.international import build_international_adapters
from legalai.packages.corpus.sources.official import build_default_priority_adapters
from legalai.packages.layers.retrieve_documents import build_bam_adapter


_QUERIES = {
    "rekabet_kurumu": "rekabet pazar fiyatlama",
    "kdk": "kamu denetçiliği idare",
    "tihek": "eşitlik ayrımcılık",
    "reklam_kurulu": "ticari reklam tüketici",
    "bam": "tazminat sözleşme",
    "dg_comp": "competition market",
    "curia": "competition market",
    "oecd_competition": "competition policy",
}


def _smoke_enabled(source_id: str) -> bool:
    return (
        os.getenv("SOCRATLEGAL_LIVE_SMOKE") == "1"
        and os.getenv(f"SOCRATLEGAL_LIVE_SMOKE_{source_id.upper()}") == "1"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("source_id", sorted(_QUERIES))
async def test_opt_in_live_source_smoke(source_id: str) -> None:
    if not _smoke_enabled(source_id):
        pytest.skip("Canlı smoke için SOCRATLEGAL_LIVE_SMOKE ve kaynak özel opt-in gerekir.")

    adapters = (
        build_bam_adapter(),
        *build_default_priority_adapters(),
        *build_international_adapters(),
    )
    adapter = next((item for item in adapters if getattr(item, "source_id", "") == source_id), None)
    if adapter is None:
        pytest.skip(f"{source_id} için yapılandırılmış adapter yok.")

    results = await adapter.search(_QUERIES[source_id], 1)
    assert all("api_key" not in str(result.metadata).lower() for result in results)
