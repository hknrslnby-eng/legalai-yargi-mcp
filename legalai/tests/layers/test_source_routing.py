from legalai.packages.layers.source_routing import build_source_query_plan


def test_competition_context_cross_queries_without_literal_keyword():
    plan = build_source_query_plan(
        question="Fiyatlama ve dagitim zincirindeki degisimlerin hukuki etkisi nedir?",
        jurisdiction_ids=["rekabet"],
        expert_lenses=["iktisat", "ticaret"],
    )

    selected = {item.source_id for item in plan.subqueries}
    assert "rekabet_kurumu" in selected
    assert "danistay" in selected
    assert "oecd_competition" in selected
    assert "curia" in selected
    assert "competition_reports" in {item.source_id for item in plan.skipped}


def test_explicit_sources_are_authoritative_and_pending_sources_are_skipped():
    plan = build_source_query_plan(
        question="Veri ihlali sonrasi idari sorumluluk",
        jurisdiction_ids=["rekabet"],
        expert_lenses=["siber"],
        selected_source_ids=["bim", "dg_comp"],
    )

    assert [item.source_id for item in plan.subqueries] == ["local_corpus", "dg_comp"]
    assert plan.skipped[0].source_id == "bim"
    assert plan.skipped[0].status == "verification_pending"


def test_trade_defense_context_includes_customs_trade_and_competition_sources():
    plan = build_source_query_plan(
        question="Ithalat baskisi ve damping marji",
        jurisdiction_ids=["ticaret_savunmasi"],
        expert_lenses=["ticaret"],
    )

    selected = {item.source_id for item in plan.subqueries}
    skipped = {item.source_id for item in plan.skipped}
    assert "ticaret_bakanligi_ithalat" in selected | skipped
    assert "wto_trade_remedy_agreements" in selected | skipped
    assert "rekabet_kurumu" in selected | skipped


def test_context_plan_is_serializable_for_pipeline_output():
    plan = build_source_query_plan(
        question="Soru",
        jurisdiction_ids=["kvkk"],
        expert_lenses=["NIS-2", "siber guvenlik"],
    )

    payload = plan.to_dict()
    assert payload["subqueries"][0]["source_id"] == "local_corpus"
    assert all("rationale" in item for item in payload["subqueries"])
