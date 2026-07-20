import pytest

import legalai.apps.mcp.server as server_module


@pytest.mark.asyncio
async def test_legal_opinion_tool_adds_13_section_contract(monkeypatch):
    class Result:
        def to_dict(self):
            return {
                "sources": [{"doc_id": "d-1", "citation": "Kaynak 1", "source": "local"}],
                "assistant_instructions": "temel talimat",
                "analysis_only": True,
                "non_binding": True,
            }

    async def fake_run_pipeline(**_kwargs):
        return Result()

    monkeypatch.setattr(server_module, "run_pipeline", fake_run_pipeline)
    payload = await server_module._socratlegal_legal_opinion_tool.fn(
        question="Sözleşmeden doğan alacak için hukukî mütalaa hazırla.",
        detail_level="exhaustive",
        max_source_quotes=5,
    )

    assert payload["mode"] == "hukuki_mutalaa"
    assert len(payload["memorandum_sections"]) == 13
    assert payload["memorandum_sections"][10].startswith("11.")
    assert payload["memorandum_sections"][11].startswith("12.")
    assert payload["memorandum_sections"][12].startswith("13.")
    assert "#d-1" in payload["assistant_instructions"]
    assert "Bütünleştirici Ayrıntılı Değerlendirme" in payload["assistant_instructions"]


def test_legal_opinion_is_discoverable():
    catalog = server_module.capability_catalog()

    assert catalog["active_public_tools"]["socratlegal_hukuki_mutalaa"] == "hukuki_mutalaa"
    assert any(item["id"] == "hukuki_mutalaa" for item in catalog["capabilities"])
