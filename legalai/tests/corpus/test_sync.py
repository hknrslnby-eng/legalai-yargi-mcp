from datetime import date

import pytest

from legalai.packages.corpus.models import CorpusDocument
from legalai.packages.corpus.sync import CorpusSyncService
from legalai.packages.corpus.store import CorpusStore


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
