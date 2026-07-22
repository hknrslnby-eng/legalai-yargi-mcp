"""RetrieveDocuments'ın gerçek ağ çağrısı YAPMADAN, enjekte edilen sahte
(fake) bir backend ile çalıştığını doğrular."""
import pytest

from legalai.packages.layers.pipeline import Context
from legalai.packages.corpus.federated import FederatedDocument, FederatedSearchResult
from legalai.packages.layers.retrieve_documents import FederatedDocumentSearchBackend, RetrieveDocuments
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


class _PlanRetriever:
    async def search_plan(self, plan, limit):
        self.plan = plan
        self.limit = limit
        return FederatedSearchResult(
            documents=(FederatedDocument("p1", "plan sonucu", "rekabet_kurumu", "RK", "", "", {}, ()),),
            errors=[],
            availability={"local_corpus": "available", "rekabet_kurumu": "available"},
        )


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


@pytest.mark.asyncio
async def test_retrieve_documents_uses_context_plan_for_federated_backend():
    retriever = _PlanRetriever()
    backend = FederatedDocumentSearchBackend(retriever=retriever)
    ctx = Context(
        tenant_id="test",
        question="Fiyatlama ve dagitim zinciri",
        mode="layered",
        jurisdiction_ids=["rekabet"],
        expert_lenses=["iktisat"],
    )

    result = await RetrieveDocuments(backend=backend, limit=7).run(ctx)

    assert retriever.limit == 7
    assert "rekabet_kurumu" in {item.source_id for item in retriever.plan.subqueries}
    assert result.source_availability["rekabet_kurumu"] == "available"
    assert result.documents[0].source == "rekabet_kurumu"
