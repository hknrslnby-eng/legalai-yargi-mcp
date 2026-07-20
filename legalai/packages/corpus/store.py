from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import aiosqlite

from .models import CorpusChunk, CorpusCitation, CorpusDocument, CorpusHit, CorpusRevision, SourceRecord, chunk_text


class CorpusStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._initialized = False

    async def _ensure(self) -> None:
        if self._initialized:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(
                """
                PRAGMA foreign_keys = ON;
                CREATE TABLE IF NOT EXISTS source_registry (
                    source_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    adapter TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    availability TEXT NOT NULL DEFAULT 'unknown',
                    availability_detail TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS corpus_documents (
                    document_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL REFERENCES source_registry(source_id),
                    title TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    institution TEXT NOT NULL,
                    body TEXT NOT NULL,
                    published_on TEXT,
                    effective_from TEXT,
                    effective_to TEXT,
                    url TEXT NOT NULL DEFAULT '',
                    citation TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS corpus_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL REFERENCES corpus_documents(document_id),
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    revision_label TEXT NOT NULL DEFAULT '',
                    fetched_at TEXT,
                    UNIQUE(document_id, content_hash)
                );
                CREATE TABLE IF NOT EXISTS corpus_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL REFERENCES corpus_documents(document_id),
                    ordinal INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    UNIQUE(document_id, ordinal)
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS corpus_fts USING fts5(
                    chunk_id UNINDEXED, text, document_id UNINDEXED, source_id UNINDEXED
                );
                CREATE TABLE IF NOT EXISTS corpus_citations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL REFERENCES corpus_documents(document_id),
                    citation_text TEXT NOT NULL,
                    quote TEXT NOT NULL DEFAULT '',
                    source_url TEXT NOT NULL DEFAULT '',
                    UNIQUE(document_id, citation_text, quote)
                );
                CREATE TABLE IF NOT EXISTS sync_cursors (
                    source_id TEXT PRIMARY KEY,
                    cursor TEXT NOT NULL
                );
                """
            )
            await db.commit()
        self._initialized = True

    @staticmethod
    def _date(value: str | None) -> date | None:
        return date.fromisoformat(value) if value else None

    async def upsert_source(self, source: SourceRecord) -> None:
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT INTO source_registry(source_id,name,adapter,source_type,availability,availability_detail,metadata_json)
                VALUES(?,?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET name=excluded.name, adapter=excluded.adapter,
                source_type=excluded.source_type, metadata_json=excluded.metadata_json""",
                (source.source_id, source.name, source.adapter, source.source_type, source.availability, source.availability_detail, json.dumps(source.metadata, ensure_ascii=False)),
            )
            await db.commit()

    async def upsert_document(self, document: CorpusDocument, *, revision: CorpusRevision | None = None, citations: list[CorpusCitation] | None = None) -> None:
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT INTO corpus_documents(document_id,source_id,title,document_type,institution,body,published_on,effective_from,effective_to,url,citation,metadata_json)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(document_id) DO UPDATE SET source_id=excluded.source_id,title=excluded.title,
                document_type=excluded.document_type,institution=excluded.institution,body=excluded.body,published_on=excluded.published_on,
                effective_from=excluded.effective_from,effective_to=excluded.effective_to,url=excluded.url,citation=excluded.citation,metadata_json=excluded.metadata_json""",
                (document.document_id, document.source_id, document.title, document.document_type, document.institution, document.body,
                 document.published_on.isoformat() if document.published_on else None, document.effective_from.isoformat() if document.effective_from else None,
                 document.effective_to.isoformat() if document.effective_to else None, document.url, document.citation, json.dumps(document.metadata, ensure_ascii=False)),
            )
            if revision:
                await db.execute(
                    "INSERT OR IGNORE INTO corpus_revisions(document_id,content,content_hash,revision_label,fetched_at) VALUES(?,?,?,?,?)",
                    (revision.document_id, revision.content, revision.content_hash, revision.revision_label, revision.fetched_at),
                )
            await db.execute("DELETE FROM corpus_chunks WHERE document_id=?", (document.document_id,))
            await db.execute("DELETE FROM corpus_fts WHERE document_id=?", (document.document_id,))
            for chunk in chunk_text(document.body):
                cursor = await db.execute("INSERT INTO corpus_chunks(document_id,ordinal,text) VALUES(?,?,?)", (document.document_id, chunk.ordinal, chunk.text))
                chunk_id = cursor.lastrowid
                await db.execute("INSERT INTO corpus_fts(chunk_id,text,document_id,source_id) VALUES(?,?,?,?)", (chunk_id, chunk.text, document.document_id, document.source_id))
            for citation in citations or []:
                await db.execute("INSERT OR IGNORE INTO corpus_citations(document_id,citation_text,quote,source_url) VALUES(?,?,?,?)", (citation.document_id, citation.citation_text, citation.quote, citation.source_url))
            await db.commit()

    async def search(self, query: str, limit: int = 20) -> list[CorpusHit]:
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            try:
                cursor = await db.execute("""SELECT d.*, s.source_id AS s_source_id, s.name AS s_name, s.adapter AS s_adapter,
                    s.source_type AS s_source_type, s.availability AS s_availability, s.availability_detail AS s_detail,
                    s.metadata_json AS s_metadata, f.chunk_id, f.text AS chunk_text FROM corpus_fts f
                    JOIN corpus_documents d ON d.document_id=f.document_id JOIN source_registry s ON s.source_id=d.source_id
                    WHERE corpus_fts MATCH ? LIMIT ?""", (query, limit))
            except Exception:
                cursor = await db.execute("""SELECT d.*, s.source_id AS s_source_id, s.name AS s_name, s.adapter AS s_adapter,
                    s.source_type AS s_source_type, s.availability AS s_availability, s.availability_detail AS s_detail,
                    s.metadata_json AS s_metadata, c.id AS chunk_id, c.text AS chunk_text FROM corpus_chunks c
                    JOIN corpus_documents d ON d.document_id=c.document_id JOIN source_registry s ON s.source_id=d.source_id
                    WHERE c.text LIKE ? LIMIT ?""", (f"%{query}%", limit))
            rows = await cursor.fetchall()
            if not rows:
                cursor = await db.execute("""SELECT d.*, s.source_id AS s_source_id, s.name AS s_name, s.adapter AS s_adapter,
                    s.source_type AS s_source_type, s.availability AS s_availability, s.availability_detail AS s_detail,
                    s.metadata_json AS s_metadata, c.id AS chunk_id, c.text AS chunk_text FROM corpus_chunks c
                    JOIN corpus_documents d ON d.document_id=c.document_id JOIN source_registry s ON s.source_id=d.source_id
                    WHERE c.text LIKE ? LIMIT ?""", (f"%{query}%", limit))
                rows = await cursor.fetchall()
        return [self._hit(row) for row in rows]

    def _hit(self, row: aiosqlite.Row) -> CorpusHit:
        document = CorpusDocument(row["document_id"], row["source_id"], row["title"], row["document_type"], row["institution"], row["body"], self._date(row["published_on"]), self._date(row["effective_from"]), self._date(row["effective_to"]), row["url"], row["citation"], json.loads(row["metadata_json"] or "{}"))
        source = SourceRecord(row["s_source_id"], row["s_name"], row["s_adapter"], row["s_source_type"], row["s_availability"], row["s_detail"], json.loads(row["s_metadata"] or "{}"))
        return CorpusHit(document, source, CorpusChunk(document.document_id, int(row["chunk_id"]), row["chunk_text"]))

    async def count(self, table: str) -> int:
        allowed = {"source_registry", "corpus_documents", "corpus_revisions", "corpus_chunks", "corpus_citations"}
        if table not in allowed:
            raise ValueError("unsupported table")
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
            row = await cursor.fetchone()
        return int(row[0])

    async def set_sync_cursor(self, source_id: str, cursor: str) -> None:
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT INTO sync_cursors(source_id,cursor) VALUES(?,?) ON CONFLICT(source_id) DO UPDATE SET cursor=excluded.cursor", (source_id, cursor))
            await db.commit()

    async def get_sync_cursor(self, source_id: str) -> str | None:
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT cursor FROM sync_cursors WHERE source_id=?", (source_id,))
            row = await cursor.fetchone()
        return row[0] if row else None

    async def set_source_availability(self, source_id: str, *, status: str, detail: str = "") -> None:
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE source_registry SET availability=?, availability_detail=? WHERE source_id=?", (status, detail, source_id))
            await db.commit()

    async def get_source(self, source_id: str) -> SourceRecord | None:
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM source_registry WHERE source_id=?", (source_id,))
            row = await cursor.fetchone()
        if not row:
            return None
        return SourceRecord(row["source_id"], row["name"], row["adapter"], row["source_type"], row["availability"], row["availability_detail"], json.loads(row["metadata_json"] or "{}"))
