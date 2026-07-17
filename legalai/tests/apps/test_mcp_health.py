import pytest

import legalai.apps.mcp.server as server_module


@pytest.mark.asyncio
async def test_legalai_health_check_is_local_and_deterministic() -> None:
    result = await server_module.legalai_saglik_kontrolu()

    assert result == {
        "status": "ok",
        "version": server_module.app.version,
        "external_calls": False,
    }
