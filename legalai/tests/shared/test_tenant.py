import asyncio

import pytest

from legalai.packages.shared.tenant import TenantContext, current_tenant, tenant_scope


@pytest.mark.asyncio
async def test_parallel_tenant_scopes_never_leak_and_restore_parent() -> None:
    parent = TenantContext("parent", "Parent")
    set_a = TenantContext("tenant-a", "A")
    set_b = TenantContext("tenant-b", "B")

    with tenant_scope(parent):
        async def worker(ctx: TenantContext) -> str:
            with tenant_scope(ctx):
                await asyncio.sleep(0)
                observed = current_tenant().tenant_id
                await asyncio.sleep(0)
                assert current_tenant().tenant_id == observed
                return observed

        observed = await asyncio.gather(
            *(worker(set_a if index % 2 == 0 else set_b) for index in range(50))
        )

        assert observed.count("tenant-a") == 25
        assert observed.count("tenant-b") == 25
        assert current_tenant().tenant_id == "parent"

