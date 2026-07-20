from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class SourceSearchResult:
    id: str
    body: str
    source_id: str
    citation: str = ""
    source_url: str = ""
    title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Provenance:
    source_id: str
    citation: str = ""
    source_url: str = ""
    retrieval_mode: str = "live"


@dataclass(frozen=True)
class FederatedDocument:
    id: str
    body: str
    source_id: str
    citation: str
    source_url: str
    title: str
    metadata: dict[str, Any]
    provenance: tuple[Provenance, ...]


@dataclass(frozen=True)
class SourceError:
    source_id: str
    error: str


@dataclass(frozen=True)
class FederatedSearchResult:
    documents: tuple[FederatedDocument, ...]
    errors: list[SourceError]
    availability: dict[str, str]


class SearchAdapter(Protocol):
    source_id: str

    async def search(self, query: str, limit: int) -> list[SourceSearchResult]: ...


class FederatedRetriever:
    def __init__(self, *, local: SearchAdapter, live: tuple[SearchAdapter, ...] = (), timeout_seconds: float = 20.0) -> None:
        self.local = local
        self.live = live
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str, limit: int = 20) -> FederatedSearchResult:
        adapters = (self.local, *self.live)
        async def run(adapter: SearchAdapter):
            try:
                return adapter.source_id, await asyncio.wait_for(adapter.search(query, limit), self.timeout_seconds), None
            except Exception as exc:
                return adapter.source_id, [], exc

        responses = await asyncio.gather(*(run(adapter) for adapter in adapters))
        merged: dict[str, FederatedDocument] = {}
        errors: list[SourceError] = []
        availability: dict[str, str] = {}
        for source_id, items, error in responses:
            if error:
                availability[source_id] = "unavailable"
                errors.append(SourceError(source_id, f"{type(error).__name__}: {error}"))
                continue
            availability[source_id] = "available"
            for item in items:
                provenance = Provenance(item.source_id, item.citation, item.source_url, "local" if item.source_id == "local" else "live")
                current = merged.get(item.id)
                if current is None:
                    merged[item.id] = FederatedDocument(item.id, item.body, item.source_id, item.citation, item.source_url, item.title, item.metadata, (provenance,))
                elif provenance not in current.provenance:
                    merged[item.id] = FederatedDocument(current.id, current.body, current.source_id, current.citation, current.source_url, current.title, current.metadata, (*current.provenance, provenance))
        return FederatedSearchResult(tuple(list(merged.values())[:limit]), errors, availability)
