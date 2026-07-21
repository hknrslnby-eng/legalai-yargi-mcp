"""Injectable adapters for international official and report collections."""
from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from legalai.packages.corpus.federated import SourceSearchResult


FetchText = Callable[[str], Awaitable[str]]


class OfficialCollectionAdapter:
    """Search an official HTML collection with source authority metadata."""

    def __init__(
        self,
        *,
        source_id: str,
        collection_urls: tuple[str, ...],
        source_kind: str,
        authority_level: str,
        fetch_text: FetchText | None = None,
        license_note: str = "",
        document_type: str = "official_document",
    ) -> None:
        self.source_id = source_id
        self.collection_urls = collection_urls
        self.source_kind = source_kind
        self.authority_level = authority_level
        self.license_note = license_note
        self.document_type = document_type
        self._fetch_text = fetch_text

    async def _fetch(self, url: str) -> str:
        if self._fetch_text is not None:
            return await self._fetch_text(url)
        import httpx

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "SocratLegal/0.1"})
            response.raise_for_status()
            return response.text

    async def search(self, query: str, limit: int) -> list[SourceSearchResult]:
        if limit <= 0:
            return []
        terms = [part.casefold() for part in query.split() if part.strip()]
        results: list[SourceSearchResult] = []
        seen: set[str] = set()
        for collection_url in self.collection_urls:
            html = await self._fetch(collection_url)
            soup = BeautifulSoup(html, "html.parser")
            for link in soup.find_all("a", href=True):
                title = " ".join(link.get_text(" ", strip=True).split())
                url = urljoin(collection_url, str(link["href"]))
                if not title or url in seen or (terms and not all(term in title.casefold() for term in terms)):
                    continue
                seen.add(url)
                detail = await self._fetch(url)
                body = " ".join(BeautifulSoup(detail, "html.parser").get_text(" ", strip=True).split())
                document_id = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
                results.append(
                    SourceSearchResult(
                        id=document_id,
                        body=body or title,
                        source_id=self.source_id,
                        citation=title,
                        source_url=url,
                        title=title,
                        metadata={
                            "document_type": self.document_type,
                            "retrieval_mode": "live",
                            "source_kind": self.source_kind,
                            "authority_level": self.authority_level,
                            "license_note": self.license_note,
                        },
                    )
                )
                if len(results) >= limit:
                    return results
        return results


class DgCompOfficialAdapter(OfficialCollectionAdapter):
    def __init__(self, *, fetch_text: FetchText | None = None) -> None:
        super().__init__(
            source_id="dg_comp",
            collection_urls=("https://competition-policy.ec.europa.eu/about/news",),
            source_kind="foreign_institution_decision",
            authority_level="comparative_institution_reference",
            fetch_text=fetch_text,
            license_note="AB Komisyonu resmi yayın koşulları korunur.",
        )


class CuriaOfficialAdapter(OfficialCollectionAdapter):
    def __init__(self, *, fetch_text: FetchText | None = None) -> None:
        super().__init__(
            source_id="curia",
            collection_urls=("https://juris.curia.europa.eu/juris/documents.jsf",),
            source_kind="foreign_judicial_decision",
            authority_level="comparative_judicial_reference",
            fetch_text=fetch_text,
            license_note="CURIA resmi yayın koşulları korunur.",
            document_type="judicial_decision",
        )


class OecdCompetitionAdapter(OfficialCollectionAdapter):
    def __init__(self, *, fetch_text: FetchText | None = None) -> None:
        super().__init__(
            source_id="oecd_competition",
            collection_urls=("https://data-explorer.oecd.org/",),
            source_kind="policy_reference",
            authority_level="non_binding_policy_reference",
            fetch_text=fetch_text,
            license_note="OECD lisans ve atıf koşulları korunur.",
            document_type="policy_report",
        )


class CompetitionReportAdapter(OfficialCollectionAdapter):
    def __init__(self, *, source_id: str = "competition_reports", fetch_text: FetchText | None = None) -> None:
        super().__init__(
            source_id=source_id,
            collection_urls=("https://competition-policy.ec.europa.eu/about/news",),
            source_kind="economic_report",
            authority_level="non_binding_economic_reference",
            fetch_text=fetch_text,
            license_note="Rapor yayımcısının lisans ve atıf koşulları korunur.",
            document_type="market_report",
        )


def build_international_adapters(*, fetch_text: FetchText | None = None) -> tuple[OfficialCollectionAdapter, ...]:
    return (
        DgCompOfficialAdapter(fetch_text=fetch_text),
        CuriaOfficialAdapter(fetch_text=fetch_text),
        OecdCompetitionAdapter(fetch_text=fetch_text),
        CompetitionReportAdapter(fetch_text=fetch_text),
    )
