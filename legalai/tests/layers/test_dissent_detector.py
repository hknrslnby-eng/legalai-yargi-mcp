import pytest

from legalai.packages.layers.dissent_detector import DissentDetector, find_dissent
from legalai.packages.layers.pipeline import Context
from legalai.packages.shared.types import Document


def test_find_dissent_returns_none_when_no_header_present():
    assert find_dissent("Sonuç olarak karar onanmıştır.") is None


def test_find_dissent_returns_text_from_header_onward():
    text = "Karar gerekçesi burada. KARŞI OY\nBen bu görüşe katılmıyorum."

    dissent = find_dissent(text)

    assert dissent is not None
    assert dissent.startswith("KARŞI OY")
    assert "katılmıyorum" in dissent


@pytest.mark.asyncio
async def test_dissent_detector_layer_populates_context():
    doc = Document(id="d1", body="Karar metni. MUHALEFET ŞERHİ\nAksi görüşteyim.")
    ctx = Context(tenant_id="test", question="q", mode="standard", documents=[doc])

    result = await DissentDetector().run(ctx)

    assert len(result.dissents) == 1
    assert result.dissents[0]["doc_id"] == "d1"
    assert result.dissents[0]["type"] == "karşı_oy"
    assert "Aksi görüşteyim" in result.dissents[0]["text"]


@pytest.mark.asyncio
async def test_dissent_detector_skips_documents_without_dissent():
    doc = Document(id="d1", body="Sadece çoğunluk görüşü var.")
    ctx = Context(tenant_id="test", question="q", mode="standard", documents=[doc])

    result = await DissentDetector().run(ctx)

    assert result.dissents == []
