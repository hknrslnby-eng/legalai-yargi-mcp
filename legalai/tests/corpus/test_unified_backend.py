import pytest

from legalai.packages.corpus.federated import FederatedDocument, FederatedSearchResult, Provenance
from legalai.packages.layers.retrieve_documents import FederatedDocumentSearchBackend


class FakeRetriever:
    async def search(self, query, limit):
        assert query == "rekabet"
        assert limit == 5
        return FederatedSearchResult(
            documents=(FederatedDocument(
                id="r-1", body="Karar metni", source_id="rekabet_kurumu", citation="RK 2026/1",
                source_url="https://example.test/r-1", title="Karar", metadata={"document_type": "decision"},
                provenance=(Provenance("local_corpus", "RK 2026/1", "https://example.test/r-1", "local"),),
            ),),
            errors=[], availability={"local_corpus": "available", "rekabet_kurumu": "available"},
        )


@pytest.mark.asyncio
async def test_federated_document_backend_keeps_provenance_in_document_metadata():
    backend = FederatedDocumentSearchBackend(retriever=FakeRetriever())

    documents = await backend.search("rekabet", 5)

    assert documents[0].id == "r-1"
    assert documents[0].source == "rekabet_kurumu"
    assert documents[0].citation == "RK 2026/1"
    assert documents[0].metadata["provenance"][0]["source_id"] == "local_corpus"
