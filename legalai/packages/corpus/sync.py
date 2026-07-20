from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Any, Iterable

from legalai.packages.shared.settings import settings

from .models import CorpusCitation, CorpusDocument, CorpusRevision, SourceRecord
from .sources.registry import SourceRegistry, default_source_registry
from .store import CorpusStore


class CorpusSyncService:
    """Safe local ingestion boundary for official/academic collections.

    Network adapters call ``ingest`` after fetching and normalizing a source.
    This keeps remote transport separate from the persistent corpus and makes
    incremental sync possible without hosting.
    """

    def __init__(self, store: CorpusStore | None = None, registry: SourceRegistry | None = None) -> None:
        self.store = store or CorpusStore(settings.corpus_db_path)
        self.registry = registry or default_source_registry()

    async def ingest(self, source_id: str, documents: Iterable[CorpusDocument]) -> dict[str, Any]:
        descriptor = self.registry.get(source_id)
        if descriptor is None:
            raise ValueError(f"Kayıtlı olmayan corpus kaynağı: {source_id}")
        await self.store.upsert_source(SourceRecord(source_id, descriptor.label, f"registry:{source_id}", descriptor.category))
        count = 0
        for document in documents:
            if document.source_id != source_id:
                raise ValueError(f"Belge kaynağı {document.source_id}, istenen kaynak {source_id} değil")
            await self.store.upsert_document(
                document,
                revision=CorpusRevision(document.document_id, document.body, document.content_hash, revision_label=date.today().isoformat()),
                citations=[CorpusCitation(document.document_id, document.citation, document.body[:500], document.url)] if document.citation else [],
            )
            count += 1
        await self.store.set_source_availability(source_id, status="available", detail=f"{count} belge işlendi")
        return {"source_id": source_id, "documents_ingested": count, "status": "available"}

    async def status(self) -> dict[str, Any]:
        return {
            "db_path": str(self.store.path),
            "documents": await self.store.count("corpus_documents"),
            "revisions": await self.store.count("corpus_revisions"),
            "chunks": await self.store.count("corpus_chunks"),
            "sources": [asdict(item) for item in self.registry.all()],
        }
