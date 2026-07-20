from __future__ import annotations

from datetime import date

import pytest

from legalai.packages.corpus.models import (
    CorpusCitation,
    CorpusDocument,
    CorpusRevision,
    SourceRecord,
    chunk_text,
    content_hash,
)
from legalai.packages.corpus.store import CorpusStore
from legalai.packages.shared.settings import Settings


def make_source() -> SourceRecord:
    return SourceRecord(
        source_id="rekabet_kurumu",
        name="Rekabet Kurumu",
        adapter="official.rekabet",
        source_type="official",
    )


def make_document(body: str = "Rekabet hukuku ve hâkim durumun kötüye kullanılması.") -> CorpusDocument:
    return CorpusDocument(
        document_id="decision-42",
        source_id="rekabet_kurumu",
        title="Competition decision",
        document_type="decision",
        institution="Rekabet Kurumu",
        body=body,
        published_on=date(2026, 7, 1),
        url="https://example.test/decision-42",
        citation="2026/42",
    )


def test_corpus_records_hash_and_chunk_deterministically() -> None:
    body = "Başlık\n\nİlk paragraf.\n\nİkinci paragraf."

    document = CorpusDocument(
        document_id="doc-1",
        source_id="local",
        title="Test",
        document_type="guidance",
        institution="Test source",
        body=body,
    )

    assert document.content_hash == content_hash(body)
    assert chunk_text(body, max_chars=30) == chunk_text(body, max_chars=30)
    assert [chunk.ordinal for chunk in chunk_text(body, max_chars=30)] == [0, 1, 2]


@pytest.mark.asyncio
async def test_upsert_is_idempotent_by_document_and_content_hash(tmp_path) -> None:
    store = CorpusStore(tmp_path / "corpus.db")
    document = make_document()
    revision = CorpusRevision(
        document_id=document.document_id,
        content=document.body,
        content_hash=document.content_hash,
        revision_label="initial",
    )
    citation = CorpusCitation(
        document_id=document.document_id,
        citation_text=document.citation,
        quote="Rekabet hukuku",
        source_url=document.url,
    )

    await store.upsert_source(make_source())
    await store.upsert_document(document, revision=revision, citations=[citation])
    await store.upsert_document(document, revision=revision, citations=[citation])

    assert await store.count("corpus_documents") == 1
    assert await store.count("corpus_revisions") == 1
    assert await store.count("corpus_chunks") > 0
    assert await store.count("corpus_citations") == 1


@pytest.mark.asyncio
async def test_fts_search_returns_provenance_preserving_hits(tmp_path) -> None:
    store = CorpusStore(tmp_path / "corpus.db")
    await store.upsert_source(make_source())
    await store.upsert_document(make_document())

    hits = await store.search("hâkim durum", limit=10)

    assert len(hits) == 1
    assert hits[0].document.document_id == "decision-42"
    assert hits[0].document.source_id == "rekabet_kurumu"
    assert hits[0].source.source_id == "rekabet_kurumu"
    assert hits[0].chunk.text


@pytest.mark.asyncio
async def test_sync_cursor_and_source_availability_are_persisted(tmp_path) -> None:
    store = CorpusStore(tmp_path / "corpus.db")
    await store.upsert_source(make_source())

    await store.set_sync_cursor("rekabet_kurumu", "page:17")
    await store.set_source_availability(
        "rekabet_kurumu", status="unavailable", detail="rate limited"
    )

    assert await store.get_sync_cursor("rekabet_kurumu") == "page:17"
    source = await store.get_source("rekabet_kurumu")
    assert source is not None
    assert source.availability == "unavailable"
    assert source.availability_detail == "rate limited"


def test_corpus_setting_has_new_default_without_changing_existing_database_settings() -> None:
    configured = Settings(_env_file=None)

    assert configured.corpus_db_path == "./.data/socratlegal_corpus.db"
    assert configured.database_url == "sqlite+aiosqlite:///./.data/legalai.db"
    assert configured.usage_db_path == "./.data/usage.db"
