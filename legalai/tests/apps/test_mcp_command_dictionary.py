import asyncio

import legalai.apps.mcp.server as server_module
from legalai.packages.discovery.commands import command_dictionary


def test_command_dictionary_has_stable_ids_aliases_examples_and_host_note():
    payload = command_dictionary()
    assert payload["commands"]["dilekce_hazirla"]["tool"] == "socratlegal_dilekce_hazirla"
    assert "legalai_dilekce_hazirla" in payload["commands"]["dilekce_hazirla"]["aliases"]
    assert payload["commands"]["onbilgi_ve_strateji"]["example_prompt"]
    assert payload["slash_command_note"]


def test_command_dictionary_resource_and_tool_are_registered():
    tools = asyncio.run(server_module.app.get_tools())
    assert "socratlegal_komut_sozlugu" in tools
    assert "legalai_komut_sozlugu" in tools
    resources = asyncio.run(server_module.app.get_resources())
    assert "socratlegal://commands" in resources
