from legalai.packages.jurisdictions.selection import guess_jurisdictions
from legalai.packages.layers.source_routing import build_source_query_plan


def test_competition_context_uses_non_literal_question_and_official_source_families():
    selection = guess_jurisdictions("Fiyatlama ve dagitim zincirindeki degisimlerin etkisi")
    plan = build_source_query_plan(
        question="Fiyatlama ve dagitim zincirindeki degisimlerin etkisi",
        jurisdiction_ids=[selection.primary, *selection.supporting],
        expert_lenses=selection.expert_lenses,
    )

    selected = {item.source_id for item in plan.subqueries}
    assert selection.primary == "rekabet"
    assert {"rekabet_kurumu", "danistay", "oecd_competition", "dg_comp", "curia", "competition_reports"} <= selected
