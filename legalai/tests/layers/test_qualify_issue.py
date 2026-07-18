import pytest

from legalai.packages.layers.pipeline import Context
from legalai.packages.layers.qualify_issue import QualifyIssue, guess_jurisdiction


def test_guess_jurisdiction_matches_hukuk_keywords():
    guess, scores = guess_jurisdiction("Vekalet ücreti nasıl hesaplanır?")

    assert guess == "hukuk"
    assert scores["hukuk"] >= 1


def test_guess_jurisdiction_returns_none_for_unmatched_text():
    guess, scores = guess_jurisdiction("bugün hava çok güzel")

    assert guess is None
    assert scores == {}


@pytest.mark.asyncio
async def test_qualify_issue_layer_sets_jurisdiction_id():
    ctx = Context(tenant_id="test", question="Vekalet ücreti nasıl hesaplanır?", mode="standard")

    result = await QualifyIssue().run(ctx)

    assert result.jurisdiction_id == "hukuk"
    assert result.jurisdiction_scores.get("hukuk", 0) >= 1


@pytest.mark.asyncio
async def test_qualify_issue_layer_does_not_override_existing_hint():
    ctx = Context(
        tenant_id="test",
        question="Vekalet ücreti nasıl hesaplanır?",
        mode="standard",
        jurisdiction_id="idare",
    )

    result = await QualifyIssue().run(ctx)

    assert result.jurisdiction_id == "idare"


@pytest.mark.asyncio
async def test_qualify_issue_layer_populates_multi_domain_selection():
    ctx = Context(
        tenant_id="test",
        question="Sözleşme alacağı için sahte belge düzenlenmiş olabilir mi?",
        mode="standard",
    )

    result = await QualifyIssue().run(ctx)

    assert set(result.jurisdiction_ids) >= {"hukuk", "ceza"}
    assert result.expert_lenses == [] or "sozlesmeler" in result.expert_lenses
