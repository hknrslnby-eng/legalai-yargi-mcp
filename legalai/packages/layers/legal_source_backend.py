"""Existing upstream legal-data clients behind LegalAI domain protocols."""
from __future__ import annotations

import re
from datetime import date
from typing import Any, Protocol

from anayasa_mcp_module.client import AnayasaMahkemesiApiClient
from anayasa_mcp_module.models import AnayasaNormDenetimiSearchRequest

from legalai.packages.layers.retrieve_documents import BedestenSearchBackend, FederatedDocumentSearchBackend
from legalai.packages.corpus.store import CorpusStore
from legalai.packages.shared.settings import settings
from legalai.packages.pii.outbound import mask_for_external
from legalai.packages.layers.temporal_context import InvalEvent, NormRecord, TemporalSourceBackend
from legalai.packages.shared.evidence import SourceScope
from legalai.packages.shared.types import Document


class DecisionBackend(Protocol):
    async def search(self, query: str, limit: int) -> list[Document]: ...


_DATE_RE = re.compile(r"(?P<day>\d{1,2})[./](?P<month>\d{1,2})[./](?P<year>\d{4})")


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    match = _DATE_RE.search(value)
    if not match:
        return None
    try:
        return date(int(match.group("year")), int(match.group("month")), int(match.group("day")))
    except ValueError:
        return None


class IntegratedLegalSourceBackend(TemporalSourceBackend):
    """Single-server adapter for decisions, AYM norms and temporal events.

    The adapter deliberately keeps unknown effective dates as ``None``. AYM
    publication is not silently treated as the exact date on which every
    affected norm ceased to apply.
    """

    def __init__(
        self,
        decision_backend: DecisionBackend | None = None,
        norm_client: Any | None = None,
        corpus_store: Any | None = None,
    ) -> None:
        self.decision_backend = decision_backend or FederatedDocumentSearchBackend()
        self.norm_client = norm_client or AnayasaMahkemesiApiClient()
        self.corpus_store = corpus_store or CorpusStore(settings.corpus_db_path)

    async def search_documents(self, query: str, limit: int = 50) -> list[Document]:
        return await self.decision_backend.search(query, limit)

    async def _search_aym_norms(self, query: str, limit: int = 10) -> list[Any]:
        query = await mask_for_external(query)
        params = AnayasaNormDenetimiSearchRequest(
            keywords_all=[query],
            results_per_page=max(1, min(limit, 10)),
        )
        result = await self.norm_client.search_norm_denetimi_decisions(params)
        return list(getattr(result, "decisions", []) or [])

    async def _official_gazette_date(self, url: str) -> date | None:
        try:
            document = await self.norm_client.get_decision_document_as_markdown(url)
        except Exception:
            return None
        return _parse_date(getattr(document, "official_gazette_info_from_page", ""))

    async def search_norms(self, query: str, on_date: date, scope: SourceScope) -> list[NormRecord]:
        del on_date, scope
        records: list[NormRecord] = []
        for decision in await self._search_aym_norms(query):
            records.append(
                NormRecord(
                    id=str(getattr(decision, "decision_page_url", "")),
                    title=str(getattr(decision, "decision_outcome_summary", "AYM norm denetimi kararı")),
                    citation=str(getattr(decision, "decision_reference_no", "")),
                    effective_from=None,
                    effective_to=None,
                    status="reference-only",
                    source_url=str(getattr(decision, "decision_page_url", "")),
                    quote=str(getattr(decision, "decision_outcome_summary", "")),
                    confidence=0.45,
                )
            )
        try:
            for hit in await self.corpus_store.search(query, 20):
                document = hit.document
                if document.document_type not in {"regulation", "legislation", "guidance", "principle_decision", "norm"}:
                    continue
                records.append(
                    NormRecord(
                        id=document.document_id,
                        title=document.title,
                        citation=document.citation,
                        effective_from=document.effective_from,
                        effective_to=document.effective_to,
                        status="active" if document.effective_to is None else "superseded",
                        source_url=document.url,
                        quote=document.body[:1000],
                        confidence=0.7,
                    )
                )
        except Exception:
            # A local corpus outage must not discard AYM/live temporal results.
            pass
        return records

    async def search_invalidation_events(
        self,
        query: str,
        date_from: date | None,
        date_to: date | None,
        scope: SourceScope,
    ) -> list[InvalEvent]:
        del date_from, date_to, scope
        events: list[InvalEvent] = []
        for decision in await self._search_aym_norms(f"{query} iptal"):
            decision_date = _parse_date(getattr(decision, "decision_date_summary", ""))
            publication_date = await self._official_gazette_date(
                str(getattr(decision, "decision_page_url", ""))
            )
            events.append(
                InvalEvent(
                    id=str(getattr(decision, "decision_page_url", "")),
                    authority="AYM",
                    decision_date=decision_date,
                    publication_date=publication_date,
                    effective_date=None,
                    effect="annulment-reference",
                    affected_norm=str(getattr(decision, "decision_outcome_summary", "")),
                    citation=str(getattr(decision, "decision_reference_no", "")),
                    source_url=str(getattr(decision, "decision_page_url", "")),
                    quote=str(getattr(decision, "decision_outcome_summary", "")),
                    confidence=0.45,
                )
            )

        if any(term in query.casefold() for term in ("iptal", "yürütmenin durdurulması", "yürütme durdurma")):
            for document in await self.decision_backend.search(
                f"{query} iptal yürütmenin durdurulması", 3
            ):
                source = str(getattr(document, "source", "")).lower()
                if "danistay" not in source:
                    continue
                body = str(getattr(document, "body", ""))
                events.append(
                    InvalEvent(
                        id=str(getattr(document, "id", "")),
                        authority="Danıştay",
                        decision_date=_parse_date(body) or _parse_date(getattr(document, "citation", "")),
                        publication_date=None,
                        effective_date=None,
                        effect="annulment-or-stay-reference",
                        affected_norm="",
                        citation=str(getattr(document, "citation", "")),
                        source_url="",
                        quote=body[:500],
                        confidence=0.3,
                    )
                )
        return events

    async def search_procedural_rules(self, query: str, scope: SourceScope) -> list[NormRecord]:
        return await self.search_norms(f"{query} süre başvuru", date.today(), scope)
