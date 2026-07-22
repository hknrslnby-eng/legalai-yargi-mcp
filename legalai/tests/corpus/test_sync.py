from datetime import date

import pytest

from legalai.packages.corpus.models import CorpusDocument
from legalai.packages.corpus.sync import CorpusSyncService
from legalai.packages.corpus.store import CorpusStore
from legalai.packages.corpus.federated import SourceSearchResult


@pytest.mark.asyncio
async def test_sync_ingests_official_collection_and_status_is_local(tmp_path):
    service = CorpusSyncService(store=CorpusStore(tmp_path / "socratlegal.db"))
    document = CorpusDocument(
        document_id="rk-1", source_id="rekabet_kurumu", title="Kurul kararı", document_type="decision",
        institution="Rekabet Kurumu", body="Hakim durum ve ilgili pazar", published_on=date(2026, 7, 1),
        url="https://example.test/rk-1", citation="RK 2026/1",
    )

    report = await service.ingest("rekabet_kurumu", [document])
    status = await service.status()

    assert report["documents_ingested"] == 1
    assert status["documents"] == 1
    assert status["db_path"].endswith("socratlegal.db")


@pytest.mark.asyncio
async def test_sync_from_adapter_masks_query_before_live_search_and_persists_result(tmp_path):
    class Adapter:
        source_id = "rekabet_kurumu"
        received_query = None

        async def search(self, query, limit):
            self.received_query = query
            return [SourceSearchResult("rk-live-1", "Karar metni", self.source_id, "RK 2026/1", "https://rk/1", "Karar", {"document_type": "decision"})]

    adapter = Adapter()
    service = CorpusSyncService(store=CorpusStore(tmp_path / "socratlegal.db"))
    report = await service.sync_from_adapter("rekabet_kurumu", adapter, "TCKN 12345678901", 5)

    assert "12345678901" not in adapter.received_query
    assert report["documents_ingested"] == 1


@pytest.mark.asyncio
async def test_ingest_persists_provenance_metadata_and_previous_content_hashes(tmp_path):
    store = CorpusStore(tmp_path / "socratlegal.db")
    service = CorpusSyncService(store=store)
    first = CorpusDocument(
        document_id="versioned-1", source_id="rekabet_kurumu", title="Karar", document_type="decision",
        institution="Rekabet Kurumu", body="Ilk metin", citation="RK 1",
        metadata={"license_note": "Atif gerekli.", "storage_policy": "metadata_or_excerpt_only"},
    )
    second = CorpusDocument(
        document_id="versioned-1", source_id="rekabet_kurumu", title="Karar", document_type="decision",
        institution="Rekabet Kurumu", body="Guncel metin", citation="RK 1",
        metadata={"license_note": "Atif gerekli.", "storage_policy": "metadata_or_excerpt_only"},
    )

    await service.ingest("rekabet_kurumu", [first])
    await service.ingest("rekabet_kurumu", [second])

    assert await store.count("corpus_revisions") == 2
    hit = (await store.search("Guncel", 1))[0]
    assert hit.document.metadata["content_hash"] == second.content_hash
    assert hit.document.metadata["license_note"] == "Atif gerekli."
    assert hit.document.metadata["storage_policy"] == "metadata_or_excerpt_only"
