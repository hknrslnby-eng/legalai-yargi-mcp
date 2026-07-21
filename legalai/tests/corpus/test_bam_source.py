from types import SimpleNamespace

import pytest

from legalai.packages.layers.retrieve_documents import BamBedestenSearchBackend


class _FakeClient:
    def __init__(self):
        self.request = None

    async def search_documents(self, request):
        self.request = request
        entry = SimpleNamespace(
            documentId="bam-1",
            itemType=SimpleNamespace(name="ISTINAFHUKUK"),
            birimAdi="BAM Hukuk Dairesi",
            esasNoYil=2025,
            esasNoSira=10,
            kararNoYil=2025,
            kararNoSira=20,
        )
        return SimpleNamespace(data=SimpleNamespace(emsalKararList=[entry]))

    async def get_document_as_markdown(self, document_id):
        return SimpleNamespace(markdown_content="BAM karar metni")


class _Backend(BamBedestenSearchBackend):
    def __init__(self, client):
        super().__init__()
        self.client = client

    def _get_client(self):
        return self.client


@pytest.mark.asyncio
async def test_bam_backend_sends_bam_item_type_and_normalizes_source():
    client = _FakeClient()
    documents = await _Backend(client).search("bayi sözleşmesi", 5)

    assert client.request.data.itemTypeList == ["ISTINAFHUKUK"]
    assert documents[0].source == "bam"
    assert documents[0].citation.startswith("BAM Hukuk Dairesi")
