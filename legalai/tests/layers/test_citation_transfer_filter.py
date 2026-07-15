import pytest

from legalai.packages.layers.citation_transfer_filter import (
    CitationTransferFilter,
    filter_transfers,
)
from legalai.packages.layers.pipeline import Context
from legalai.packages.shared.types import Document


def test_filter_transfers_removes_marker_sentences():
    text = "Davacı vekili zararın tazminini talep etmiştir. Dairemizce inceleme yapılmıştır."

    kept, transferred = filter_transfers(text)

    assert "Dairemizce inceleme yapılmıştır." in kept
    assert "Davacı vekili" not in kept
    assert len(transferred) == 1


@pytest.mark.asyncio
async def test_citation_transfer_filter_layer_mutates_document_body():
    doc = Document(
        id="d1",
        body="Davalı zararın oluşmadığını savunmuştur. Sonuç olarak karar onanmıştır.",
    )
    ctx = Context(tenant_id="test", question="q", mode="standard", documents=[doc])

    result = await CitationTransferFilter().run(ctx)

    assert "onanmıştır" in result.documents[0].body
    assert "Davalı" not in result.documents[0].body
