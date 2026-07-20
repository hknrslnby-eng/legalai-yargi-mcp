from __future__ import annotations

from legalai.packages.contracts import extract_contract
from legalai.packages.contracts.review import build_issue_matrix, classify_contract, route_personas


def test_mixed_contract_uses_dominant_element_and_mohuk_priority():
    intake = extract_contract(
        text="ARTICLE 1 Distribution; English law; EUR payment; exclusive territory"
    )

    result = classify_contract(intake)

    assert result.legal_nature == "mixed_distribution"
    assert result.classification_method == "dominant_element"
    assert result.foreign_law_layer == "mohuk_priority"


def test_router_has_negative_reason_for_non_invoked_kvkk():
    intake = extract_contract(text="MADDE 1 Satış bedeli ve teslim tarihi")
    classification = classify_contract(intake)

    kvkk = next(
        item for item in route_personas(classification, intake) if item.persona_id == "kvkk"
    )

    assert kvkk.invoked is False
    assert kvkk.negative_reason


def test_issue_matrix_contains_general_contract_gaps_and_clause_context():
    intake = extract_contract(text="MADDE 1 - Bedel\nAlıcı bedeli öder.")
    classification = classify_contract(intake)
    routes = route_personas(classification, intake)

    issues = build_issue_matrix(intake, classification, routes)
    issue_ids = {issue.issue_id for issue in issues}

    assert "clause-1" in issue_ids
    assert "termination" in issue_ids
    assert "dispute_resolution" in issue_ids
    assert all(issue.personas for issue in issues)
