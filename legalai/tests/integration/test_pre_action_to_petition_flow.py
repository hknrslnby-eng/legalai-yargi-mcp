from legalai.packages.layers.pre_action_strategy import PreActionRequest, analyze_pre_action
from legalai.packages.petitions.models import PetitionRequest
from legalai.packages.petitions.service import process_petition


def test_triggering_notice_flows_into_source_safe_petition_draft():
    intake = analyze_pre_action(
        PreActionRequest(
            document_text="TEBLİGAT: 7 gün içinde cevap veriniz. Dava dilekçesi ve sözleşme ektedir.",
            mode="full_intake",
            question="Davalı olarak tüm dava dışı ve dava içi yolları değerlendir.",
            event_dates=["2026-07-20"],
        )
    )
    petition = process_petition(
        PetitionRequest(
            operation="draft",
            petition_text=None,
            question="Bu tebligata karşı cevap dilekçesi hazırla.",
            party_position="davalı",
            jurisdiction_hint="hukuk",
            event_dates=intake.dates,
        )
    )
    assert intake.priorities[0]["id"] == "P0"
    assert any(item["route"] == "Avukatlık Kanunu 35/A" for item in intake.strategy_options)
    assert petition.quality["party_position"] == "davalı"
    assert any(section["id"] == "talep_sonucu" for section in petition.sections)
    assert petition.analysis_only and petition.non_binding
