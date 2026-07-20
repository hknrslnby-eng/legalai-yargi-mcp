import asyncio

import legalai.apps.mcp.server as server_module


def test_high_value_tools_expose_parameter_descriptions_to_mcp_clients():
    tools = asyncio.run(server_module.app.get_tools())

    hudoc = tools["aihm_karar_getir"].parameters["properties"]
    opinion = tools["socratlegal_hukuki_mutalaa"].parameters["properties"]
    layered = tools["katmanli_analiz"].parameters["properties"]
    petition = tools["socratlegal_bilirkisi_raporu_dilekce"].parameters["properties"]
    contract = tools["socratlegal_sozlesme_incele"].parameters["properties"]

    assert hudoc["application_no"]["description"]
    assert hudoc["lang"]["description"]
    assert opinion["detail_level"]["description"]
    assert opinion["max_source_quotes"]["description"]
    assert layered["question"]["description"]
    assert petition["file_path"]["description"]
    assert contract["detail_level"]["description"]
