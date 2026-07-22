import pytest

from legalai.packages.shared.types import Document
import legalai.apps.mcp.server as server_module


class _FakeSourceBackend:
    seen_plan = None

    async def search_plan(self, plan, limit):
        self.seen_plan = plan
        if any(item.source_id == "bim" for item in plan.skipped):
            return [], {"local_corpus": "available", "bim": "skipped:verification_pending"}, []
        return [Document("source-1", "Resmi karar metni", "rekabet_kurumu", "RK 2026/1", "https://source/1", {"provenance": [{"source_id": "rekabet_kurumu"}]})], {
            "local_corpus": "available",
            "rekabet_kurumu": "available",
        }, []


@pytest.mark.asyncio
async def test_source_search_returns_plan_availability_provenance_and_non_binding(monkeypatch):
    backend = _FakeSourceBackend()
    monkeypatch.setattr(server_module, "FederatedDocumentSearchBackend", lambda: backend)

    payload = await server_module.socratlegal_kaynak_ara.fn(
        question="Fiyatlama ve dagitim zinciri",
        jurisdiction_hint="rekabet",
        limit=7,
    )

    assert "rekabet_kurumu" in {item.source_id for item in backend.seen_plan.subqueries}
    assert payload["source_query_plan"]["subqueries"][0]["rationale"]
    assert payload["source_availability"]["rekabet_kurumu"] == "available"
    assert payload["documents"][0]["metadata"]["provenance"]
    assert payload["analysis_only"] is True
    assert payload["non_binding"] is True


@pytest.mark.asyncio
async def test_source_search_keeps_pending_bim_out_of_live_documents(monkeypatch):
    backend = _FakeSourceBackend()
    monkeypatch.setattr(server_module, "FederatedDocumentSearchBackend", lambda: backend)

    payload = await server_module.socratlegal_kaynak_ara.fn(
        question="Idari yargi sorusu",
        selected_source_ids=["bim"],
    )

    assert payload["documents"] == []
    assert payload["source_availability"]["bim"] == "skipped:verification_pending"
    assert payload["source_query_plan"]["skipped"][0]["source_id"] == "bim"
