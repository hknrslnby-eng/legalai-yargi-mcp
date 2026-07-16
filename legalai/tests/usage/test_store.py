from datetime import datetime, timezone

import pytest

from legalai.packages.usage.store import UsageStore


@pytest.mark.asyncio
async def test_usage_report_filters_by_month_and_tenant(tmp_path) -> None:
    store = UsageStore(tmp_path / "usage.db")
    await store.record(
        tenant_id="local",
        model="gemini-2.5-pro",
        input_tokens=100,
        output_tokens=20,
        cost_usd_estimate=1.25,
        ts=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )
    await store.record(
        tenant_id="test_isolation",
        model="gemini-2.5-pro",
        input_tokens=200,
        output_tokens=30,
        cost_usd_estimate=2.5,
        ts=datetime(2026, 7, 2, tzinfo=timezone.utc),
    )
    await store.record(
        tenant_id="local",
        model="gemini-2.5-pro",
        input_tokens=999,
        output_tokens=999,
        cost_usd_estimate=9.99,
        ts=datetime(2026, 6, 30, tzinfo=timezone.utc),
    )

    report = await store.report("2026-07", tenant_id="local")

    assert report["calls"] == 1
    assert report["input_tokens"] == 100
    assert report["output_tokens"] == 20
    assert report["cost_usd_estimate"] == pytest.approx(1.25)
    assert report["by_model"]["gemini-2.5-pro"]["calls"] == 1

