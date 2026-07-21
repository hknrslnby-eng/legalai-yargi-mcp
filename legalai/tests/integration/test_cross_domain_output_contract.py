from legalai.packages.petitions.models import PetitionRequest
from legalai.packages.petitions.service import process_petition


def test_cross_domain_petition_output_keeps_positive_negative_effects_and_ledger():
    result = process_petition(
        PetitionRequest(
            operation="lengthen",
            petition_text="İşlem nedeniyle zarar doğmuştur.",
            question="Ceza soruşturması, idari başvuru ve tazminat stratejisini birlikte değerlendir.",
            party_position="mağdur",
            jurisdiction_hint="ceza, idare, hukuk",
            event_dates=["2026-01-01"],
            source_documents=[{"id": "source-1", "citation": "Örnek künye", "quote": "Örnek alıntı"}],
        )
    )
    domains = {item["domain_id"] for item in result.cross_domain_inquiry["branches"]}
    assert {"ceza", "idare", "hukuk"} <= domains
    assert all(branch["positive_effects"] and branch["negative_effects"] for branch in result.cross_domain_inquiry["branches"])
    assert result.evidence_ledger[0]["source_id"] == "source-1"
    assert result.lengthening_safeguards["new_facts_allowed"] is False
