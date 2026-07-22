from __future__ import annotations

from dataclasses import asdict, replace
from datetime import date, datetime, timezone
import re
from typing import Any, Iterable

from legalai.packages.shared.settings import settings

from .models import CorpusCitation, CorpusDocument, CorpusRevision, SourceRecord
from .federated import SourceSearchResult
from legalai.packages.pii.outbound import mask_for_external
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
            fetched_at = datetime.now(timezone.utc).isoformat()
            enriched = replace(document, metadata={
                **document.metadata,
                "source_id": source_id,
                "document_id": document.document_id,
                "content_hash": document.content_hash,
                "retrieval_mode": document.metadata.get("retrieval_mode", "corpus_ingest"),
                "storage_policy": document.metadata.get("storage_policy", "full_text"),
                "license_note": document.metadata.get("license_note", ""),
                "fetched_at": fetched_at,
                "version": document.metadata.get("version", date.today().isoformat()),
            })
            await self.store.upsert_document(
                enriched,
                revision=CorpusRevision(enriched.document_id, enriched.body, enriched.content_hash, revision_label=date.today().isoformat(), fetched_at=fetched_at),
                citations=[CorpusCitation(enriched.document_id, enriched.citation, enriched.body[:500], enriched.url)] if enriched.citation else [],
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

    async def sync_from_adapter(self, source_id: str, adapter: Any, query: str, limit: int = 20) -> dict[str, Any]:
        """Search one live adapter and persist its normalized public results."""
        masked_query = await mask_for_external(query)
        # Keep a conservative identifier boundary even when a malformed TCKN
        # fails the checksum-aware PII matcher.
        masked_query = re.sub(r"\b\d{11}\b", "[TCKN_MASKELENDI]", masked_query)
        results: list[SourceSearchResult] = await adapter.search(masked_query, limit)
        documents = [
            CorpusDocument(
                document_id=result.id,
                source_id=source_id,
                title=result.title or result.citation or result.id,
                document_type=str(result.metadata.get("document_type", "decision")),
                institution=source_id,
                body=result.body,
                url=result.source_url,
                citation=result.citation,
                metadata={
                    **result.metadata,
                    "source_id": source_id,
                    "document_id": result.id,
                    "retrieval_mode": "live_sync",
                    "storage_policy": result.metadata.get("storage_policy", "full_text"),
                    "license_note": result.metadata.get("license_note", ""),
                },
            )
            for result in results
        ]
        return await self.ingest(source_id, documents)
