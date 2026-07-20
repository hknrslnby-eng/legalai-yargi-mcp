from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class SourceRecord:
    source_id: str
    name: str
    adapter: str
    source_type: str
    availability: str = "unknown"
    availability_detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CorpusDocument:
    document_id: str
    source_id: str
    title: str
    document_type: str
    institution: str
    body: str
    published_on: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    url: str = ""
    citation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        return content_hash(self.body)


@dataclass(frozen=True)
class CorpusChunk:
    document_id: str
    ordinal: int
    text: str


@dataclass
class CorpusRevision:
    document_id: str
    content: str
    content_hash: str
    revision_label: str = ""
    fetched_at: str | None = None


@dataclass
class CorpusCitation:
    document_id: str
    citation_text: str
    quote: str = ""
    source_url: str = ""


@dataclass(frozen=True)
class CorpusHit:
    document: CorpusDocument
    source: SourceRecord
    chunk: CorpusChunk


def content_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def chunk_text(value: str, max_chars: int = 1200) -> list[CorpusChunk]:
    paragraphs = [part.strip() for part in value.split("\n\n") if part.strip()]
    if not paragraphs:
        paragraphs = [value.strip()] if value.strip() else []
    chunks: list[CorpusChunk] = []
    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            chunks.append(CorpusChunk("", len(chunks), paragraph))
            continue
        for offset in range(0, len(paragraph), max_chars):
            chunks.append(CorpusChunk("", len(chunks), paragraph[offset : offset + max_chars]))
    return chunks
