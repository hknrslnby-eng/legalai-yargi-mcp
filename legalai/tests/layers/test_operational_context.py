from legalai.packages.layers.operational_context import OperationalContextBuilder
from legalai.packages.layers.operational_lenses import build_operational_findings


def test_mining_license_workflow_maps_technical_process_to_legal_impacts():
    context = OperationalContextBuilder().build("Maden arama ruhsatı, izinler ve saha projesi")

    finding = context.findings[0]
    assert finding.domain == "technical_regulatory_process"
    assert finding.evidence_status == "hypothesis"
    assert finding.legal_impacts
    assert context.unknowns


def test_iban_crypto_workflow_uses_role_hypotheses_without_stereotypes():
    findings, unknowns = build_operational_findings(question="IBAN kiralama, kripto borsası ve soğuk cüzdan transferi")

    assert {item.domain for item in findings} >= {"financial_crypto_flow", "behavioural_process"}
    assert any(item.evidence_status == "verification_required" for item in findings)
    assert all("fakir" not in item.statement.lower() for item in findings)
    assert unknowns


def test_cyber_and_competition_findings_keep_legal_impacts_separate_and_visible():
    context = OperationalContextBuilder().build(
        "Siber veri ihlali ve fiyatlama/dagitim pazar etkisi",
        ["rekabet", "kvkk"],
    )

    domains = {item["domain"] for item in context.to_dict()["findings"]}
    assert {"cybersecurity_incident", "commercial_market_operations"} <= domains
    assert all(item["legal_impacts"] for item in context.to_dict()["findings"])
