import pytest

import legalai.apps.mcp.server as server_module
from legalai.packages.discovery.catalog import capability_catalog


def test_catalog_advertises_eight_legal_output_languages():
    payload = capability_catalog()
    assert payload["supported_output_languages"] == ["tr", "en", "fr", "de", "ru", "ar", "es", "zh"]


@pytest.mark.asyncio
async def test_opinion_tool_accepts_non_turkish_output_language(monkeypatch):
    async def fake_run_pipeline(**kwargs):
        class Result:
            def to_dict(self):
                return {"sources": [], "operational_context": {}, "missing_facts": [], "assistant_instructions": "base"}
        return Result()

    monkeypatch.setattr(server_module, "run_pipeline", fake_run_pipeline)
    payload = await server_module._socratlegal_legal_opinion_tool.fn(
        question="Soru", output_language="fr", server_side_synthesis=False,
    )

    assert "Çıktı dili: fr" in payload["assistant_instructions"]
