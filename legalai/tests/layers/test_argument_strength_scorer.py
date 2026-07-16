import pytest

from legalai.packages.layers.argument_strength_scorer import (
    ArgumentStrengthScorer,
    hierarchy_weight,
    ratio_length_weight,
)
from legalai.packages.layers.pipeline import Context
from legalai.packages.shared.types import Document

_HUKUK_HIERARCHY = ["IBK", "HGK", "DAIRE", "BAM", "ILK_DERECE"]


def test_hierarchy_weight_prefers_higher_levels():
    ibk_score = hierarchy_weight("Yargıtay İBK 2020/1 E.", _HUKUK_HIERARCHY)
    daire_score = hierarchy_weight("Yargıtay 3. Dairesi 2023/1 E.", _HUKUK_HIERARCHY)
    unknown_score = hierarchy_weight("Belirsiz bir mahkeme kararı", _HUKUK_HIERARCHY)

    assert ibk_score > daire_score > unknown_score


def test_hierarchy_weight_without_hierarchy_returns_neutral():
    assert hierarchy_weight("herhangi bir metin", []) == 0.5


def test_ratio_length_weight_caps_at_one():
    assert ratio_length_weight("x" * 10000) == 1.0
    assert ratio_length_weight("") == 0.0
    assert 0 < ratio_length_weight("x" * 250) < 1.0


@pytest.mark.asyncio
async def test_argument_strength_scorer_penalizes_dissenting_documents():
    strong_doc = Document(id="strong", body="", citation="Yargıtay HGK 2023/1 E.")
    weak_doc = Document(id="weak", body="", citation="İlk Derece Mahkemesi kararı")

    ctx = Context(
        tenant_id="test",
        question="soru",
        mode="layered",
        jurisdiction_id="hukuk",
        documents=[strong_doc, weak_doc],
        ratios=[
            {"doc_id": "strong", "text": "x" * 600},
            {"doc_id": "weak", "text": "kısa"},
        ],
        dissents=[{"doc_id": "strong", "text": "karşı oy", "type": "karşı_oy"}],
    )

    result = await ArgumentStrengthScorer().run(ctx)

    by_id = {s["doc_id"]: s["strength"] for s in result.argument_scores}
    assert set(by_id) == {"strong", "weak"}
    # HGK + uzun ratio ama karşı oy cezalı; ilk derece + kısa ratio'dan hâlâ güçlü olmalı.
    assert by_id["strong"] > by_id["weak"]


@pytest.mark.asyncio
async def test_argument_strength_scorer_handles_missing_jurisdiction():
    doc = Document(id="d1", body="", citation="bir karar")
    ctx = Context(tenant_id="test", question="soru", mode="layered", documents=[doc])

    result = await ArgumentStrengthScorer().run(ctx)

    assert result.argument_scores[0]["doc_id"] == "d1"
