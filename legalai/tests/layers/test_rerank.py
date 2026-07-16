import pytest

from legalai.packages.layers.pipeline import Context
from legalai.packages.layers.rerank import Rerank, score_document
from legalai.packages.shared.types import Document


def test_score_document_returns_zero_for_empty_query():
    assert score_document(set(), "herhangi bir metin") == 0.0


def test_score_document_returns_overlap_ratio():
    query_tokens = {"zarar", "tazminat", "kusur"}
    score = score_document(query_tokens, "Bu kararda zarar ve kusur tespit edilmiştir.")
    assert score == pytest.approx(2 / 3)


@pytest.mark.asyncio
async def test_rerank_orders_documents_by_overlap_and_trims_to_top_k():
    low = Document(id="low", body="ilgisiz bir metin")
    high = Document(id="high", body="zarar tazminat kusur davası hakkında karar")
    mid = Document(id="mid", body="zarar hakkında bir cümle")
    ctx = Context(
        tenant_id="test",
        question="zarar tazminat kusur",
        mode="layered",
        documents=[low, high, mid],
    )

    result = await Rerank(top_k=2).run(ctx)

    assert [doc.id for doc in result.documents] == ["high", "mid"]
    assert result.scored[0]["doc_id"] == "high"
    assert len(result.scored) == 3  # skorlar trim öncesi tüm belgeler için tutulur


@pytest.mark.asyncio
async def test_rerank_handles_empty_documents():
    ctx = Context(tenant_id="test", question="soru", mode="layered", documents=[])

    result = await Rerank(top_k=5).run(ctx)

    assert result.documents == []
    assert result.scored == []
