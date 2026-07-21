import pytest

import legalai.apps.mcp.server as server_module


@pytest.mark.asyncio
async def test_legalai_help_returns_selectable_capabilities_and_examples() -> None:
    payload = await server_module.legalai_yardim()

    capability_ids = {item["id"] for item in payload["capabilities"]}
    assert {"katmanli_analiz", "agresif_karsi_taraf", "derin_arastirma"} <= capability_ids
    assert any("bilirkişi" in item.lower() for item in payload["planned_capabilities"])
    assert all(item["example_prompt"] for item in payload["capabilities"])
    assert payload["privacy"]["outbound_masking"] is True
    assert payload["analysis_only"] is True


def test_mcp_prompts_are_available_for_plain_and_refined_workflows() -> None:
    assert "karşı taraf" in server_module.agresif_karsi_taraf_promptu.fn().lower()
    assert "çözüm" in server_module.cozum_stratejisi_promptu.fn().lower()
    assert "bilirkişi" in server_module.bilir_kisi_raporu_itirazi_promptu.fn().lower()


def test_capability_resource_has_direct_python_facade() -> None:
    assert "capabilities" in server_module.legalai_capabilities_resource()


def test_pre_action_legacy_alias_is_registered() -> None:
    import asyncio

    tools = asyncio.run(server_module.app.get_tools())
    assert "socratlegal_onbilgi_ve_strateji" in tools
    assert "legalai_onbilgi_ve_strateji" in tools
