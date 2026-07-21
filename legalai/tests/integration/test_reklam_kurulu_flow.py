import pytest

from legalai.packages.corpus.sources.official import ReklamKuruluOfficialAdapter
from legalai.packages.jurisdictions.persona import compose_persona_instructions


@pytest.mark.asyncio
async def test_reklam_kurulu_live_adapter_and_persona_are_connected():
    pages = {
        "https://ticaret.gov.tr/tuketici/ticari-reklamlar/reklam-kurulu-kararlari": '<a href="/karar/1">Reklam Kurulu 369 sayılı karar</a>',
        "https://ticaret.gov.tr/karar/1": "Tüketiciyi yanıltıcı reklam iddiası incelendi.",
    }

    async def fetch(url: str) -> str:
        return pages[url]

    result = await ReklamKuruluOfficialAdapter(fetch_text=fetch).search("reklam", 5)
    persona = compose_persona_instructions(["reklam_kurulu"])
    assert result and result[0].metadata["institution"] == "Reklam Kurulu"
    assert "tüketici" in persona.casefold()
    assert "reklam" in persona.casefold()
