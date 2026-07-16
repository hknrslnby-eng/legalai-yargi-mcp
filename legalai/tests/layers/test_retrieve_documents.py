"""RetrieveDocuments'ın gerçek ağ çağrısı YAPMADAN, enjekte edilen sahte
(fake) bir backend ile çalıştığını doğrular."""
import pytest

from legalai.packages.layers.pipeline import Context
from legalai.packages.layers.retrieve_documents import RetrieveDocuments
from legalai.packages.shared.types import Document


class _FakeBackend:
    def __init__(self, documents=None, error=None):
        self._documents = documents or []
        self._error = error
        self.received_query = None
        self.received_limit = None

    async def search(self, query, limit):
        self.received_query = query
        self.received_limit = limit
        if self._error:
            raise self._error
        return self._documents


@pytest.mark.asyncio
async def test_retrieve_documents_calls_backend_with_question_and_limit():
    backend = _FakeBackend(documents=[Document(id="d1", body="karar metni")])
    ctx = Context(tenant_id="test", question="zarar tazminatı", mode="layered")

    result = await RetrieveDocuments(backend=backend, limit=50).run(ctx)

    assert backend.received_query == "zarar tazminatı"
    assert backend.received_limit == 50
    assert [d.id for d in result.documents] == ["d1"]


@pytest.mark.asyncio
async def test_retrieve_documents_skips_search_when_documents_already_present():
    backend = _FakeBackend(documents=[Document(id="should-not-be-used", body="")])
    existing = Document(id="fixture-1", body="zaten verilmiş belge")
    ctx = Context(tenant_id="test", question="soru", mode="layered", documents=[existing])

    result = await RetrieveDocuments(backend=backend).run(ctx)

    assert result.documents == [existing]
    assert backend.received_query is None  # backend hiç çağrılmadı


@pytest.mark.asyncio
async def test_retrieve_documents_records_error_without_crashing_pipeline():
    backend = _FakeBackend(error=RuntimeError("ağ hatası"))
    ctx = Context(tenant_id="test", question="soru", mode="layered")

    result = await RetrieveDocuments(backend=backend).run(ctx)

    assert result.documents == []
    assert any(t.get("layer") == "retrieve_documents" and "error" in t for t in result.trace)
