import asyncio
from datetime import datetime, timezone

import pytest

from legalai.packages.pii.gateway import PiiGateway
from legalai.packages.shared.tenant import TenantContext, tenant_scope
from legalai.packages.usage.store import UsageStore


@pytest.mark.asyncio
async def test_fifty_parallel_jobs_keep_pii_and_usage_tenant_isolated(tmp_path) -> None:
    pii = PiiGateway(tmp_path / "pii_map.db")
    usage = UsageStore(tmp_path / "usage.db")
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    tenants = {
        "local": TenantContext("local", "Local"),
        "test_isolation": TenantContext("test_isolation", "Isolation"),
    }
    semaphore = asyncio.Semaphore(10)

    async def worker(tenant_id: str, index: int) -> None:
        async with semaphore:
            ctx = tenants[tenant_id]
            other = tenants["test_isolation" if tenant_id == "local" else "local"]
            original = f"TCKN {10000000000 + index + (0 if tenant_id == 'local' else 50)}"
            with tenant_scope(ctx):
                masked = await pii.mask(original)
                assert await pii.unmask_from_store(masked) == original
                await usage.record(
                    tenant_id=tenant_id,
                    model="test-model",
                    input_tokens=index + 1,
                    output_tokens=2,
                    cost_usd_estimate=0.01,
                )
            with tenant_scope(other):
                assert await pii.unmask_from_store(masked) == masked

    await asyncio.gather(
        *(worker(tenant_id, index) for tenant_id in tenants for index in range(50))
    )

    local_report = await usage.report(month, tenant_id="local")
    isolated_report = await usage.report(month, tenant_id="test_isolation")

    assert local_report["calls"] == 50
    assert isolated_report["calls"] == 50
    assert local_report["input_tokens"] == 1275
    assert isolated_report["input_tokens"] == 1275

