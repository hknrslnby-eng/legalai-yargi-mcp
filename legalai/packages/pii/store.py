"""SQLite `pii_map` tablosu — tenant_id sütunlu, DEK zarf şifrelemeli.
Bkz. FORK-KAPSAMLI-PLAN.md §7 (multi-tenancy checklist, "PII mapping" satırı)."""
from __future__ import annotations

import pathlib

import aiosqlite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS pii_map (
    tenant_id TEXT NOT NULL,
    token TEXT NOT NULL,
    encrypted_value TEXT NOT NULL,
    wrapped_dek TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (tenant_id, token)
);
"""


async def _connect(db_path: pathlib.Path | str) -> aiosqlite.Connection:
    path = pathlib.Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(path)
    await conn.execute(_SCHEMA)
    await conn.commit()
    return conn


async def put_token(
    tenant_id: str,
    token: str,
    encrypted_value: str,
    wrapped_dek: str,
    db_path: pathlib.Path | str,
) -> None:
    conn = await _connect(db_path)
    try:
        await conn.execute(
            "INSERT OR REPLACE INTO pii_map (tenant_id, token, encrypted_value, wrapped_dek) "
            "VALUES (?, ?, ?, ?)",
            (tenant_id, token, encrypted_value, wrapped_dek),
        )
        await conn.commit()
    finally:
        await conn.close()


async def get_token(
    tenant_id: str, token: str, db_path: pathlib.Path | str
) -> tuple[str, str] | None:
    """`(encrypted_value, wrapped_dek)` döner; bulunamazsa `None`."""
    conn = await _connect(db_path)
    try:
        cursor = await conn.execute(
            "SELECT encrypted_value, wrapped_dek FROM pii_map WHERE tenant_id = ? AND token = ?",
            (tenant_id, token),
        )
        row = await cursor.fetchone()
        return (row[0], row[1]) if row else None
    finally:
        await conn.close()
