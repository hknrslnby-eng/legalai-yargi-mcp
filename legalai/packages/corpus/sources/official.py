"""Thin, injectable adapters around upstream-derived official clients.

These wrappers own normalization and provenance. They intentionally do not
modify the upstream clients or their public APIs.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import hashlib
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

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


class OfficialHtmlCollectionAdapter:
    """Search an official public collection page without changing upstream code.

    ``fetch_text`` is injectable for tests and for institutions whose site
    requires a custom transport. The default uses a short-lived httpx client.
    Collection pages are only discovery surfaces; each matching detail URL is
    fetched and retained as provenance.
    """

    def __init__(self, *, source_id: str, collection_urls: tuple[str, ...], fetch_text: Any | None = None) -> None:
        self.source_id = source_id
        self.collection_urls = collection_urls
        self._fetch_text = fetch_text

    async def _fetch(self, url: str) -> str:
        if self._fetch_text is not None:
            return await self._fetch_text(url)
        import httpx

        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers={"User-Agent": "SocratLegal/0.1"}) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    async def search(self, query: str, limit: int) -> list[SourceSearchResult]:
        terms = [part.casefold() for part in query.split() if part.strip()]
        results: list[SourceSearchResult] = []
        seen: set[str] = set()
        for collection_url in self.collection_urls:
            try:
                html = await self._fetch(collection_url)
            except Exception:
                continue
            soup = BeautifulSoup(html, "html.parser")
            for link in soup.find_all("a", href=True):
                title = " ".join(link.get_text(" ", strip=True).split())
                url = urljoin(collection_url, str(link["href"]))
                if not title or url in seen or (terms and not all(term in title.casefold() for term in terms)):
                    continue
                seen.add(url)
                try:
                    detail = await self._fetch(url)
                    body = " ".join(BeautifulSoup(detail, "html.parser").get_text(" ", strip=True).split())
                except Exception:
                    body = title
                document_id = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
                results.append(SourceSearchResult(document_id, body or title, self.source_id, title, url, title, {"document_type": "decision", "retrieval_mode": "live"}))
                if len(results) >= limit:
                    return results
        return results


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
    adapters.append(
        KeywordGatedAdapter(
            OfficialHtmlCollectionAdapter(
                source_id="kdk",
                collection_urls=("https://ombudsman.gov.tr/KararYayinlarimiz",),
            ),
            ("kamu denetçiliği", "ombudsman", "tavsiye kararı", "idare"),
        )
    )
    adapters.append(
        KeywordGatedAdapter(
            OfficialHtmlCollectionAdapter(
                source_id="tihek",
                collection_urls=(
                    "https://cocuk.tihek.gov.tr/kategori/pages/kararlar",
                    "https://uom.tihek.gov.tr/kategori/pages/kararlar",
                ),
            ),
            ("tihek", "ayrımcılık", "eşitlik", "insan hakları"),
        )
    )
    return tuple(adapters)
