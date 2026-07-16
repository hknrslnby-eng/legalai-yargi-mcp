"""`POST /api/v1/analyze`'in `run_pipeline`'ı çağırdığını doğrular —
gerçek ağ/LLM çağrısı yapmaz (`run_pipeline` monkeypatch edilir)."""
import pytest
from httpx import ASGITransport, AsyncClient

import legalai.apps.api.routes as routes_module
from legalai.apps.api.app import app
from legalai.packages.layers.analysis_pipeline import AnalysisResult
from legalai.packages.shared.types import Document


async def _fake_run_pipeline(question, mode="layered", jurisdiction_hint=None, documents=None, pipeline=None):
    return AnalysisResult(
        question=question,
        mode=mode,
        jurisdiction_id=jurisdiction_hint or "hukuk",
        answer=f"cevap: {question} [#d1]",
        citations=["d1"],
        ratios=[],
        dictums=[],
        dissents=[],
        argument_scores=[],
        documents=[Document(id="d1", body="", citation="Yargıtay 1. HD", source="yargitay")],
        trace=[],
    )


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_analyze_endpoint_returns_pipeline_result(monkeypatch):
    monkeypatch.setattr(routes_module, "run_pipeline", _fake_run_pipeline)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/analyze", json={"question": "zarar tazminatı"})

    assert response.status_code == 200
    body = response.json()
    assert body["citations"] == ["d1"]
    assert body["sources"] == [{"doc_id": "d1", "citation": "Yargıtay 1. HD", "source": "yargitay"}]
    assert "zarar tazminatı" in body["answer"]


@pytest.mark.asyncio
async def test_analyze_endpoint_rejects_empty_question():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/analyze", json={"question": ""})

    assert response.status_code == 422
