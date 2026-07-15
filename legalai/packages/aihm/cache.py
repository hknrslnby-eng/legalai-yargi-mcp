"""AİHM kararları için basit SQLite cache — 30 gün TTL.

Bkz. FORK-KAPSAMLI-PLAN.md §4.3: "`tenant_id='_shared'` — herkes için
ortak, çünkü kamu bilgisi." Bu yüzden bu cache'te tenant_id sütunu YOK;
AİHM kararları herkese açık kamu verisidir, tenant izolasyonu gerektirmez.

Not: `legalai.packages.shared.settings` henüz kurulmadı (bu, Hafta
1-3'ün kapsamı dışında bırakıldı). Bu modül şimdilik sabit bir varsayılan
yol kullanıyor; Settings modülü kurulduğunda buradaki `CACHE_DB_PATH`
`settings.storage_root`'a bağlanacak (bkz. §2.4).
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import aiosqlite

CACHE_DB_PATH = pathlib.Path("./.data/aihm_cache.db")
TTL_SECONDS = 30 * 24 * 3600  # 30 gün

_SCHEMA = """
CREATE TABLE IF NOT EXISTS aihm_cache (
    cache_key TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    fetched_at REAL NOT NULL
)
"""


async def _connect(db_path: pathlib.Path) -> aiosqlite.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(db_path)
    await conn.execute(_SCHEMA)
    await conn.commit()
    return conn


async def get_cached(cache_key: str, db_path: pathlib.Path = CACHE_DB_PATH) -> dict[str, Any] | None:
    conn = await _connect(db_path)
    try:
        cursor = await conn.execute(
            "SELECT payload, fetched_at FROM aihm_cache WHERE cache_key = ?", (cache_key,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        payload, fetched_at = row
        if time.time() - fetched_at > TTL_SECONDS:
            return None
        return json.loads(payload)
    finally:
        await conn.close()


async def set_cached(cache_key: str, payload: dict[str, Any], db_path: pathlib.Path = CACHE_DB_PATH) -> None:
    conn = await _connect(db_path)
    try:
        await conn.execute(
            "INSERT INTO aihm_cache (cache_key, payload, fetched_at) VALUES (?, ?, ?) "
            "ON CONFLICT(cache_key) DO UPDATE SET payload = excluded.payload, fetched_at = excluded.fetched_at",
            (cache_key, json.dumps(payload, ensure_ascii=False), time.time()),
        )
        await conn.commit()
    finally:
        await conn.close()
