import pytest

from legalai.packages.bilirkisi.workflow import analyze_report, build_petition_draft
from legalai.packages.layers.memorandum import MEMORANDUM_SECTIONS, MemorandumProfile, build_memorandum_instructions
from legalai.packages.petitions.models import PetitionRequest
from legalai.packages.petitions.service import process_petition


def test_memorandum_keeps_13_sections_and_subordinates_operational_context_to_law():
    instructions = build_memorandum_instructions(
        MemorandumProfile(),
        operational_context={"findings": [{"legal_impacts": ["nedensellik"]}]},
        missing_facts=["Pazar paylari ve ilgili urun pazari"],
    )

    positions = [instructions.index(section) for section in MEMORANDUM_SECTIONS]
    assert positions == sorted(positions)
    assert "Operasyonel/teknik bulguları ayrı bir katman" in instructions
    assert "Eksik veri taleplerini" in instructions
    assert "Atıf politikası: retain" in instructions


def test_petition_shortening_retains_citations_by_default_and_requires_approval_for_removal():
    petition = "Yargıtay 2024/1 E. 2025/2 K. kararı uyarınca talep sonucu korunmalıdır."
    retained = process_petition(PetitionRequest("shorten", petition))

    assert retained.citation_change_report[0].action == "retained"
    assert retained.citation_change_report[0].user_approved is False

    with pytest.raises(PermissionError):
        process_petition(PetitionRequest("shorten", petition, citation_policy="remove"))
    removed = process_petition(PetitionRequest("shorten", petition, citation_policy="remove", citation_removal_approved=True))
    assert removed.citation_change_report[0].action == "removed"
    assert removed.citation_change_report[0].user_approved is True


@pytest.mark.asyncio
async def test_bilirkişi_analysis_and_petition_share_operational_context():
    analysis = await analyze_report(
        text="Ölçüm kesin kabul edilmiştir; kalibrasyon kaydı gösterilmemiştir.",
        question="Bu teknik sonuca itiraz et.",
        technical_domain="mühendislik",
    )
    draft = build_petition_draft(analysis, court="Mahkeme")

    assert analysis.operational_context["findings"]
    assert draft.operational_context == analysis.operational_context
