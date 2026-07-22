from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from legalai.packages.pii.outbound import mask_for_external

if TYPE_CHECKING:
    from legalai.packages.layers.source_routing import SourceQueryPlan


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
        return await self._search_adapters(((adapter, query) for adapter in adapters), limit=limit)

    async def search_plan(self, plan: SourceQueryPlan, limit: int = 20) -> FederatedSearchResult:
        """Run the planned local and source-specific queries.

        A legacy ``KeywordGatedAdapter`` is unwrapped here so a source is
        selected by the plan's context rather than by a literal query token.
        """
        adapters_by_source = {self.local.source_id: self.local}
        adapters_by_source.update({adapter.source_id: adapter for adapter in self.live})
        requests: list[tuple[SearchAdapter, str]] = []
        availability: dict[str, str] = {}
        errors: list[SourceError] = []
        for subquery in plan.subqueries:
            adapter = adapters_by_source.get(subquery.source_id)
            if adapter is None:
                availability[subquery.source_id] = "unconfigured"
                errors.append(SourceError(subquery.source_id, "No adapter configured"))
                continue
            if subquery.source_id not in {"local", "local_corpus"}:
                adapter = getattr(adapter, "adapter", adapter)
            requests.append((adapter, subquery.query))
        for skipped in plan.skipped:
            availability[skipped.source_id] = f"skipped:{skipped.status}"
        result = await self._search_adapters(requests, limit=limit)
        return FederatedSearchResult(
            result.documents,
            [*errors, *result.errors],
            {**availability, **result.availability},
        )

    async def _search_adapters(self, requests: Any, *, limit: int) -> FederatedSearchResult:
        requests = tuple(requests)
        async def run(adapter: SearchAdapter, query: str):
            try:
                external_query = await mask_for_external(query)
                external_query = re.sub(r"\b\d{11}\b", "[TCKN_MASKELENDI]", external_query)
                adapter_query = query if adapter.source_id in {"local", "local_corpus"} else external_query
                return adapter.source_id, await asyncio.wait_for(adapter.search(adapter_query, limit), self.timeout_seconds), None
            except Exception as exc:
                return adapter.source_id, [], exc

        responses = await asyncio.gather(*(run(adapter, query) for adapter, query in requests))
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
