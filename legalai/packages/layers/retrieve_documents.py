"""RetrieveDocuments — soruyla ilgili gerçek karar metinlerini getirir.
Bkz. FORK-KAPSAMLI-PLAN.md §5.3 ("RetrieveDocuments 50"), Hafta 7.

Varsayılan backend, upstream yargi-mcp'nin zaten sahip olduğu
`bedesten_mcp_module` istemcisini kullanır (Bedesten API: Yargıtay +
Danıştay birleşik tam metin arama) — ayrı bir vektör veritabanı (pgvector/
qdrant, bkz. §8.2) henüz kurulmadığı için bu, "gerçek DB'de bulunan"
belgeleri getirmenin en basit yoludur.

`ctx.documents` çağırıdan önce zaten doldurulmuşsa (örn. test fixture'ı
veya `decision_id` ile doğrudan belge akışı) bu katman HİÇBİR ŞEY YAPMAZ —
var olan belgeleri ezmez.
"""
from __future__ import annotations

import logging
from typing import Protocol

from legalai.packages.layers.pipeline import Context
from legalai.packages.corpus.federated import FederatedRetriever, SourceSearchResult
from legalai.packages.corpus.store import CorpusStore
from legalai.packages.corpus.sources.official import build_default_priority_adapters
from legalai.packages.pii.outbound import mask_for_external
from legalai.packages.shared.settings import settings
from legalai.packages.shared.types import Document

logger = logging.getLogger(__name__)


class DocumentSearchBackend(Protocol):
    async def search(self, query: str, limit: int) -> list[Document]: ...


class BedestenSearchBackend:
    """Varsayılan backend: Bedesten API (Yargıtay + Danıştay) tam metin arama.

    Ağ hatalarını kasıtlı olarak yutmaz — çağıran katman (`RetrieveDocuments`)
    hatayı yakalayıp `ctx.trace`'e not düşer, böylece pipeline tamamen
    çökmez ama neden belgesiz kaldığı izlenebilir kalır.
    """

    def __init__(self, item_types: list[str] | None = None) -> None:
        self._item_types = item_types or ["YARGITAYKARARI", "DANISTAYKARAR"]
        self._client = None  # lazy — testlerde ağ bağımlılığı tetiklenmesin

    def _get_client(self):
        if self._client is None:
            from bedesten_mcp_module.client import BedestenApiClient

            self._client = BedestenApiClient()
        return self._client

    async def search(self, query: str, limit: int) -> list[Document]:
        from bedesten_mcp_module.models import BedestenSearchData, BedestenSearchRequest

        client = self._get_client()
        query = await mask_for_external(query)
        page_size = max(1, min(limit, 10))
        request = BedestenSearchRequest(
            data=BedestenSearchData(
                pageSize=page_size,
                pageNumber=1,
                itemTypeList=self._item_types,
                phrase=query,
            )
        )
        response = await client.search_documents(request)
        entries = response.data.emsalKararList if response.data else []

        documents: list[Document] = []
        for entry in entries[:limit]:
            markdown = await client.get_document_as_markdown(entry.documentId)
            esas = f"{entry.esasNoYil}/{entry.esasNoSira} E." if entry.esasNoYil else ""
            karar = f"{entry.kararNoYil}/{entry.kararNoSira} K." if entry.kararNoYil else ""
            citation = " ".join(p for p in [entry.birimAdi or "", esas, karar] if p)
            documents.append(
                Document(
                    id=entry.documentId,
                    body=markdown.markdown_content or "",
                    source=entry.itemType.name.lower(),
                    citation=citation,
                )
            )
        return documents


class _LocalCorpusAdapter:
    source_id = "local_corpus"

    def __init__(self, store: CorpusStore) -> None:
        self.store = store

    async def search(self, query: str, limit: int) -> list[SourceSearchResult]:
        hits = await self.store.search(query, limit)
        return [
            SourceSearchResult(
                id=hit.document.document_id,
                body=hit.document.body,
                source_id=hit.document.source_id,
                citation=hit.document.citation,
                source_url=hit.document.url,
                title=hit.document.title,
                metadata={"retrieval_mode": "local", "document_type": hit.document.document_type},
            )
            for hit in hits
        ]


class _DocumentBackendAdapter:
    def __init__(self, backend: DocumentSearchBackend, source_id: str = "bedesten") -> None:
        self.backend = backend
        self.source_id = source_id

    async def search(self, query: str, limit: int) -> list[SourceSearchResult]:
        documents = await self.backend.search(query, limit)
        return [
            SourceSearchResult(
                id=document.id,
                body=document.body,
                source_id=document.source or self.source_id,
                citation=document.citation,
                source_url=document.source_url,
                metadata={"retrieval_mode": "live", **(document.metadata or {})},
            )
            for document in documents
        ]


class FederatedDocumentSearchBackend:
    """Local corpus + live official search compatibility backend.

    The local SQLite corpus is optional. Bedesten remains a live branch, so a
    user who has not downloaded Yargıtay/Danıştay/AYM/AİHM material still gets
    the upstream live search path.
    """

    def __init__(self, retriever: FederatedRetriever | None = None) -> None:
        if retriever is not None:
            self._retriever = retriever
            return
        store = CorpusStore(settings.corpus_db_path)
        self._retriever = FederatedRetriever(
            local=_LocalCorpusAdapter(store),
            live=(_DocumentBackendAdapter(BedestenSearchBackend()), *build_default_priority_adapters()),
        )

    async def search(self, query: str, limit: int) -> list[Document]:
        result = await self._retriever.search(query, limit)
        return [
            Document(
                id=document.id,
                body=document.body,
                source=document.source_id,
                citation=document.citation,
                source_url=document.source_url,
                metadata={
                    **document.metadata,
                    "provenance": [
                        {
                            "source_id": item.source_id,
                            "citation": item.citation,
                            "source_url": item.source_url,
                            "retrieval_mode": item.retrieval_mode,
                        }
                        for item in document.provenance
                    ],
                    "source_availability": result.availability,
                    "source_errors": [error.__dict__ for error in result.errors],
                },
            )
            for document in result.documents
        ]


class RetrieveDocuments:
    name = "retrieve_documents"

    def __init__(self, backend: DocumentSearchBackend | None = None, limit: int = 50) -> None:
        self._backend = backend or FederatedDocumentSearchBackend()
        self._limit = limit

    async def run(self, ctx: Context) -> Context:
        if ctx.documents:
            return ctx

        try:
            ctx.documents = await self._backend.search(ctx.question, self._limit)
        except Exception as exc:  # ağ/parse hatası — belgesiz devam, üst katman not düşer
            logger.warning("RetrieveDocuments: arama başarısız: %s", exc)
            ctx.trace.append({"layer": self.name, "error": str(exc)})
        return ctx
