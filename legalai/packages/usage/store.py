"""SQLite-backed tenant usage records and monthly reports."""
from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import aiosqlite

from legalai.packages.shared.settings import settings


_MONTH_RE = re.compile(r"^(?P<year>\d{4})-(?P<month>0[1-9]|1[0-2])$")
_SCHEMA = """
CREATE TABLE IF NOT EXISTS usage_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd_estimate REAL NOT NULL,
    ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_usage_records_tenant_ts
    ON usage_records (tenant_id, ts);
"""


@dataclass(frozen=True)
class UsageRecord:
    tenant_id: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd_estimate: float
    ts: datetime


class UsageStore:
    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        self.db_path = pathlib.Path(db_path or settings.usage_db_path)

    async def _connect(self) -> aiosqlite.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(self.db_path)
        await conn.executescript(_SCHEMA)
        await conn.commit()
        return conn

    async def record(
        self,
        tenant_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd_estimate: float,
        ts: datetime | None = None,
    ) -> None:
        if not tenant_id.strip():
            raise ValueError("tenant_id boş olamaz")
        if not model.strip():
            raise ValueError("model boş olamaz")
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("token sayıları negatif olamaz")
        if cost_usd_estimate < 0:
            raise ValueError("maliyet negatif olamaz")
        timestamp = ts or datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        timestamp = timestamp.astimezone(timezone.utc)

        conn = await self._connect()
        try:
            await conn.execute(
                "INSERT INTO usage_records "
                "(tenant_id, model, input_tokens, output_tokens, cost_usd_estimate, ts) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    tenant_id,
                    model,
                    int(input_tokens),
                    int(output_tokens),
                    float(cost_usd_estimate),
                    timestamp.isoformat(),
                ),
            )
            await conn.commit()
        finally:
            await conn.close()

    async def report(self, month: str, tenant_id: str | None = None) -> dict[str, Any]:
        if not _MONTH_RE.fullmatch(month):
            raise ValueError("month YYYY-MM biçiminde olmalı")

        conn = await self._connect()
        try:
            where = ["ts LIKE ?"]
            params: list[Any] = [f"{month}-%"]
            if tenant_id is not None:
                where.append("tenant_id = ?")
                params.append(tenant_id)
            clause = " AND ".join(where)
            totals_cursor = await conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(input_tokens), 0), "
                "COALESCE(SUM(output_tokens), 0), COALESCE(SUM(cost_usd_estimate), 0) "
                f"FROM usage_records WHERE {clause}",
                params,
            )
            totals = await totals_cursor.fetchone()
            rows_cursor = await conn.execute(
                "SELECT model, COUNT(*), COALESCE(SUM(input_tokens), 0), "
                "COALESCE(SUM(output_tokens), 0), COALESCE(SUM(cost_usd_estimate), 0) "
                f"FROM usage_records WHERE {clause} GROUP BY model ORDER BY model",
                params,
            )
            rows = await rows_cursor.fetchall()
            return {
                "month": month,
                "tenant_id": tenant_id,
                "calls": int(totals[0]),
                "input_tokens": int(totals[1]),
                "output_tokens": int(totals[2]),
                "cost_usd_estimate": float(totals[3]),
                "by_model": {
                    row[0]: {
                        "calls": int(row[1]),
                        "input_tokens": int(row[2]),
                        "output_tokens": int(row[3]),
                        "cost_usd_estimate": float(row[4]),
                    }
                    for row in rows
                },
            }
        finally:
            await conn.close()
