import pytest

import legalai.apps.mcp.server as server_module
from legalai.packages.contracts.models import ContractReviewRequest
from legalai.packages.contracts.review import review_contract


@pytest.mark.asyncio
async def test_socratlegal_contract_tool_exposes_review_payload(monkeypatch):
    captured = {}

    async def fake_runner(**_kwargs):
        class Result:
            def to_dict(self):
                return {"evidence": [], "temporal_context": None, "operational_context": {}}

        return Result()

    async def fake_review(request: ContractReviewRequest):
        captured["request"] = request
        result = await review_contract(request, pipeline_runner=fake_runner)
        return result

    monkeypatch.setattr(server_module, "review_contract", fake_review)
    payload = await server_module._socratlegal_contract_review_tool.fn(
        contract_text="MADDE 1 Bedel",
        purpose="risk taraması",
        position="kiracı",
        detail_level="deep",
    )

    assert payload["analysis_only"] is True
    assert payload["non_binding"] is True
    assert captured["request"].purpose == "risk taraması"
    assert captured["request"].detail_level == "deep"


@pytest.mark.asyncio
async def test_legacy_contract_tool_is_exact_compatibility_alias(monkeypatch):
    calls = []

    async def fake_socratlegal(**kwargs):
        calls.append(kwargs)
        return {"analysis_only": True, "non_binding": True}

    class ToolLike:
        fn = staticmethod(fake_socratlegal)

    monkeypatch.setattr(server_module, "_socratlegal_contract_review_tool", ToolLike())
    payload = await server_module._legacy_legalai_contract_review_tool.fn(contract_text="MADDE 1 Bedel")

    assert payload["analysis_only"] is True
    assert calls[0]["contract_text"] == "MADDE 1 Bedel"


def test_catalog_marks_contract_review_active():
    catalog = server_module.capability_catalog()

    assert catalog["active_public_tools"]["socratlegal_sozlesme_incele"] == "sozlesme_incele"
    capability = next(item for item in catalog["capabilities"] if item["id"] == "sozlesme_incele")
    assert capability["example_prompt"]
    assert "sözleşme inceleme" not in catalog["planned_capabilities"]
