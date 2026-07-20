import pytest

import legalai.apps.mcp.server as server_module


PUBLIC_ANALYSIS_TOOLS = {
    "socratlegal_katmanli_analiz",
    "socratlegal_agresif_karsi_taraf",
    "socratlegal_derin_arastirma",
    "socratlegal_bilirkisi_raporu_analiz",
    "socratlegal_bilirkisi_raporu_dilekce",
}


@pytest.mark.asyncio
async def test_public_server_brand_and_tool_names_are_socratlegal() -> None:
    tool_names = set(await server_module.app.get_tools())

    assert server_module.app.name == "SocratLegal MCP Server"
    assert server_module.capability_catalog()["brand"] == "SocratLegal"
    assert PUBLIC_ANALYSIS_TOOLS <= tool_names


@pytest.mark.asyncio
async def test_legacy_legalai_analysis_names_remain_registered_aliases() -> None:
    tool_names = set(await server_module.app.get_tools())

    assert {
        "legalai_katmanli_analiz",
        "legalai_agresif_karsi_taraf",
        "legalai_derin_arastirma",
        "legalai_bilirkisi_raporu_analiz",
        "legalai_bilirkisi_raporu_dilekce",
    } <= tool_names


@pytest.mark.asyncio
async def test_public_help_and_health_facades_are_available() -> None:
    help_payload = await server_module.socratlegal_yardim()
    health_payload = await server_module.socratlegal_saglik_kontrolu()

    assert help_payload["brand"] == "SocratLegal"
    assert health_payload == {
        "status": "ok",
        "version": server_module.app.version,
        "external_calls": False,
    }


@pytest.mark.asyncio
async def test_public_bilirkişi_tools_are_production_tools() -> None:
    payload = await server_module._socratlegal_bilirkisi_analysis_tool.fn(
        report_text="Kalibrasyon incelenmeden ölçüm kesin kabul edilmiştir.",
        question="Bu bilirkişi raporuna itiraz et.",
        technical_domain="mühendislik",
    )

    assert payload["production_enabled"] is True
    assert payload["claims"]
    assert "planned" not in str(payload).lower()
