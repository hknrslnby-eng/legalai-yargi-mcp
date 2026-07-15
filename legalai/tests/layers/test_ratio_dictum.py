import pytest

from legalai.packages.layers.pipeline import Context
from legalai.packages.layers.ratio_dictum import RatioDictumFilter, split_ratio_dictum
from legalai.packages.shared.types import Document


def test_split_ratio_dictum_separates_dictum_sentences():
    text = (
        "Dairemizce yapılan incelemede zarar tespit edilmiştir. "
        "Hemen ifade edelim ki bu görüş bağlayıcı değildir. "
        "Sonuç olarak karar onanmıştır."
    )

    ratio, dictum = split_ratio_dictum(text)

    assert "bağlayıcı değildir" in dictum
    assert "onanmıştır" in ratio
    assert "bağlayıcı değildir" not in ratio


def test_split_ratio_dictum_empty_text_returns_empty_strings():
    ratio, dictum = split_ratio_dictum("")
    assert ratio == ""
    assert dictum == ""


@pytest.mark.asyncio
async def test_ratio_dictum_filter_layer_populates_context():
    doc = Document(id="d1", body="Sonuç olarak karar onanmıştır. Hemen ifade edelim ki bu bir örnektir.")
    ctx = Context(tenant_id="test", question="q", mode="standard", documents=[doc])

    result = await RatioDictumFilter().run(ctx)

    assert len(result.ratios) == 1
    assert len(result.dictums) == 1
    assert result.ratios[0]["doc_id"] == "d1"
    assert "onanmıştır" in result.ratios[0]["text"]
    assert "örnektir" in result.dictums[0]["text"]
