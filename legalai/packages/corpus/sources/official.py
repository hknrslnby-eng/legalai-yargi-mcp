"""Thin, injectable adapters around upstream-derived official clients.

These wrappers own normalization and provenance. They intentionally do not
modify the upstream clients or their public APIs.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from legalai.packages.corpus.federated import SourceSearchResult


def _value(item: Any, name: str, default: str = "") -> str:
    value = item.get(name, default) if isinstance(item, dict) else getattr(item, name, default)
    return str(value or default)


class RekabetOfficialAdapter:
    source_id = "rekabet_kurumu"

    def __init__(self, client: Any) -> None:
        self.client = client

    async def search(self, query: str, limit: int) -> list[SourceSearchResult]:
        from rekabet_mcp_module.models import RekabetKurumuSearchRequest

        result = await self.client.search_decisions(RekabetKurumuSearchRequest(PdfText=query, page=1))
        items: list[SourceSearchResult] = []
        for summary in list(getattr(result, "decisions", []) or [])[:limit]:
            decision_id = _value(summary, "karar_id") or _value(summary, "decision_number") or _value(summary, "title")
            body = _value(summary, "title")
            if decision_id and hasattr(self.client, "get_decision_document"):
                document = await self.client.get_decision_document(decision_id)
                body = _value(document, "markdown_chunk") or body
            items.append(SourceSearchResult(decision_id, body, self.source_id, _value(summary, "decision_number"), _value(summary, "decision_url"), _value(summary, "title"), {"document_type": "decision"}))
        return items


class KvkkOfficialAdapter:
    source_id = "kvkk"

    def __init__(self, client: Any) -> None:
        self.client = client

    async def search(self, query: str, limit: int) -> list[SourceSearchResult]:
        from kvkk_mcp_module.models import KvkkSearchRequest

        result = await self.client.search_decisions(KvkkSearchRequest(keywords=query, page=1, pageSize=min(limit, 10)))
        items: list[SourceSearchResult] = []
        for summary in list(getattr(result, "decisions", []) or [])[:limit]:
            url = _value(summary, "url")
            decision_id = _value(summary, "decision_id") or url or _value(summary, "title")
            body = _value(summary, "description") or _value(summary, "title")
            if url and hasattr(self.client, "get_decision_document"):
                document = await self.client.get_decision_document(url)
                body = _value(document, "markdown_chunk") or body
            items.append(SourceSearchResult(decision_id, body, self.source_id, _value(summary, "decision_number"), url, _value(summary, "title"), {"document_type": "decision"}))
        return items


class KikOfficialAdapter:
    source_id = "kik"

    def __init__(self, client: Any) -> None:
        self.client = client

    async def search(self, query: str, limit: int) -> list[SourceSearchResult]:
        result = await self.client.search_decisions(karar_metni=query)
        items: list[SourceSearchResult] = []
        for summary in list(getattr(result, "decisions", []) or [])[:limit]:
            decision_id = _value(summary, "gundemMaddesiId") or _value(summary, "kararNo")
            body = " ".join(filter(None, (_value(summary, "basvuruKonusu"), _value(summary, "karar"))))
            if decision_id and hasattr(self.client, "get_document_markdown"):
                document = await self.client.get_document_markdown(decision_id)
                body = _value(document, "markdown_chunk") or body
            items.append(SourceSearchResult(decision_id, body, self.source_id, _value(summary, "kararNo"), "", _value(summary, "basvuruKonusu"), {"document_type": "decision"}))
        return items


@dataclass(frozen=True)
class ConfiguredSource:
    source_id: str
    adapter: Any
    enabled: bool = True


class KeywordGatedAdapter:
    def __init__(self, adapter: Any, keywords: tuple[str, ...]) -> None:
        self.adapter = adapter
        self.source_id = adapter.source_id
        self.keywords = keywords

    async def search(self, query: str, limit: int) -> list[SourceSearchResult]:
        if not any(keyword.casefold() in query.casefold() for keyword in self.keywords):
            return []
        return await self.adapter.search(query, limit)


def priority_adapters(*, rekabet_client: Any | None = None, kvkk_client: Any | None = None, kik_client: Any | None = None) -> tuple[Any, ...]:
    adapters: list[Any] = []
    if rekabet_client is not None:
        adapters.append(RekabetOfficialAdapter(rekabet_client))
    if kvkk_client is not None:
        adapters.append(KvkkOfficialAdapter(kvkk_client))
    if kik_client is not None:
        adapters.append(KikOfficialAdapter(kik_client))
    return tuple(adapters)


def build_default_priority_adapters() -> tuple[Any, ...]:
    """Build safe live adapters without using upstream fallback secrets.

    Rekabet and KİK are public site adapters. KVKK is enabled only when the
    caller explicitly provides BRAVE_API_TOKEN; otherwise it remains a local
    corpus source until configured.
    """
    if os.getenv("SOCRATLEGAL_ENABLE_OFFICIAL_ADAPTERS", "true").casefold() in {"0", "false", "no"}:
        return ()
    adapters: list[Any] = []
    try:
        from rekabet_mcp_module.client import RekabetKurumuApiClient

        adapters.append(KeywordGatedAdapter(RekabetOfficialAdapter(RekabetKurumuApiClient()), ("rekabet", "kartel", "hakim durum", "birleşme", "pazar")))
    except Exception:
        pass
    try:
        from kik_mcp_module.client_v2 import KikV2ApiClient

        adapters.append(KeywordGatedAdapter(KikOfficialAdapter(KikV2ApiClient()), ("ihale", "kamu ihale", "ekap", "4734")))
    except Exception:
        pass
    if os.getenv("BRAVE_API_TOKEN"):
        try:
            from kvkk_mcp_module.client import KvkkApiClient

            adapters.append(KeywordGatedAdapter(KvkkOfficialAdapter(KvkkApiClient()), ("kvkk", "kişisel veri", "veri sorumlusu", "açık rıza")))
        except Exception:
            pass
    return tuple(adapters)
