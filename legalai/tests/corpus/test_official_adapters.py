import pytest

from legalai.packages.corpus.sources.official import KikOfficialAdapter, KvkkOfficialAdapter, RekabetOfficialAdapter


class FakeClient:
    def __init__(self, summary, document):
        self.summary = summary
        self.document = document
        self.requests = []

    async def search_decisions(self, request=None, **kwargs):
        self.requests.append((request, kwargs))
        return type("Result", (), {"decisions": [self.summary]})()

    async def get_decision_document(self, identifier):
        self.requests.append(("fetch", identifier))
        return self.document

    async def get_document_markdown(self, identifier):
        self.requests.append(("fetch", identifier))
        return self.document


@pytest.mark.asyncio
async def test_rekabet_adapter_normalizes_summary_and_full_text():
    client = FakeClient(type("Summary", (), {"karar_id": "42", "decision_number": "2026/1", "decision_url": "https://rk/42", "title": "İlgili pazar"})(), type("Doc", (), {"markdown_chunk": "Tam karar"})())
    results = await RekabetOfficialAdapter(client).search("ilgili pazar", 5)
    assert results[0].source_id == "rekabet_kurumu"
    assert results[0].body == "Tam karar"
    assert results[0].citation == "2026/1"


@pytest.mark.asyncio
async def test_kvkk_adapter_uses_masked_search_boundary_upstream_contract():
    client = FakeClient(type("Summary", (), {"decision_id": "kvkk-1", "decision_number": "2026/1", "url": "https://kvkk/1", "title": "Açık rıza", "description": "özet"})(), type("Doc", (), {"markdown_chunk": "KVKK karar metni"})())
    results = await KvkkOfficialAdapter(client).search("açık rıza", 5)
    assert results[0].source_id == "kvkk"
    assert results[0].body == "KVKK karar metni"


@pytest.mark.asyncio
async def test_kik_adapter_normalizes_decision_and_fetches_document():
    client = FakeClient(type("Summary", (), {"gundemMaddesiId": "7", "kararNo": "2026/UH.1", "basvuruKonusu": "İhale"})(), type("Doc", (), {"markdown_chunk": "KİK karar metni"})())
    results = await KikOfficialAdapter(client).search("ihale", 5)
    assert results[0].source_id == "kik"
    assert results[0].body == "KİK karar metni"
