import pytest

from legalai.packages.usage.store import UsageStore


@pytest.mark.asyncio
async def test_usage_report_rejects_invalid_month(tmp_path) -> None:
    store = UsageStore(tmp_path / "usage.db")

    with pytest.raises(ValueError, match="YYYY-MM"):
        await store.report("July 2026")

