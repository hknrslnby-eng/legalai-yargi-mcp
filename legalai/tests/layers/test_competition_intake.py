import pytest

from legalai.packages.layers.competition_intake import build_competition_intake
from legalai.packages.layers.pipeline import Context, Pipeline
from legalai.packages.layers.pre_action_strategy import PreActionRequest, analyze_pre_action
from legalai.packages.layers.analysis_pipeline import run_pipeline


def test_competition_intake_requests_maximum_relevant_economic_facts():
    intake = build_competition_intake(
        question="Birlesme sonrasi fiyatlama ve dagitim kisitlari",
        known_facts={"relevant_product_market": "endustriyel yazilim"},
    )

    keys = {item.key for item in intake.requested_facts}
    assert {"relevant_geographic_market", "market_shares_by_year", "sales_volume_by_year", "sales_revenue_by_year"} <= keys
    assert {"competitors", "suppliers", "customers", "value_chain_position", "entry_barriers", "sector_reports"} <= keys
    assert {"transaction_structure", "pricing_strategy", "distribution_terms"} <= keys
    assert "rekabet_kurumu" in intake.source_families
    assert "competition_reports" in intake.source_families
    assert all(item.question and item.rationale for item in intake.requested_facts)


def test_pre_action_adds_competition_missing_facts_without_blocking_analysis():
    result = analyze_pre_action(PreActionRequest(
        question="Fiyatlama ve pazar payi etkisini incele",
        mode="triage",
    ))

    assert any("relevant_product_market" in item for item in result.missing_facts)
    assert any(item["id"] == "COMP_market_shares_by_year" for item in result.questions)
    assert result.analysis_only is True


class _CompetitionLayer:
    name = "competition_fixture"

    async def run(self, ctx: Context) -> Context:
        ctx.jurisdiction_id = "rekabet"
        ctx.jurisdiction_ids = ["rekabet"]
        return ctx


@pytest.mark.asyncio
async def test_layered_analysis_exposes_competition_intake_and_missing_facts():
    result = await run_pipeline(
        "Fiyatlama ve dagitim zincirindeki degisimler",
        pipeline=Pipeline([_CompetitionLayer()]),
        synthesize=False,
    )

    assert result.competition_intake is not None
    assert result.missing_facts
    assert result.to_dict()["competition_intake"]["requested_facts"]
