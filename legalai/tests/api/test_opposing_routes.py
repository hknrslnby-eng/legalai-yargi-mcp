import pytest
from httpx import ASGITransport, AsyncClient

import legalai.apps.api.routes as routes_module
from legalai.apps.api.app import app
from legalai.packages.layers.opposing import OpposingResult


async def _fake_run_opposing(**kwargs):
    return OpposingResult(
        question=kwargs["question"],
        mode="host-orchestrated",
        role=kwargs["role"],
        position=kwargs["position"],
        assistant_instructions="nonbinding analysis",
    )


@pytest.mark.asyncio
async def test_opposing_endpoint_returns_structured_nonbinding_result(monkeypatch):
    monkeypatch.setattr(routes_module, "run_opposing", _fake_run_opposing)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/opposing",
            json={"question": "alacak", "position": "ödenmedi", "role": "davacı"},
        )

    assert response.status_code == 200
    assert response.json()["analysis_only"] is True
    assert response.json()["non_binding"] is True
    assert response.json()["source_scope"] == "targeted"
