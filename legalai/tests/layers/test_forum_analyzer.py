from legalai.packages.jurisdictions.base import JurisdictionProfile
from legalai.packages.layers.forum_analyzer import ForumAndDeadlineAnalyzer
from legalai.packages.shared.temporal import TemporalLegalContext


def test_debt_question_returns_ranked_court_enforcement_and_mediation_options() -> None:
    profile = JurisdictionProfile(
        id="hukuk",
        name="Hukuk",
        raw={
            "competent_forums": [
                {"kind": "mahkeme", "name": "Asliye Hukuk Mahkemesi", "basis": "profil"}
            ]
        },
    )

    candidates = ForumAndDeadlineAnalyzer().analyze(
        "Ödenmeyen alacağımı nasıl tahsil ederim?",
        TemporalLegalContext.from_question("Ödenmeyen alacağımı nasıl tahsil ederim?"),
        profile,
    )

    kinds = {candidate.kind for candidate in candidates}
    assert "mahkeme" in kinds
    assert "icra_dairesi" in kinds
    assert "arabuluculuk" in kinds
    assert all(candidate.confidence <= 1 for candidate in candidates)


def test_missing_facts_keep_multiple_forum_alternatives_and_uncertainty() -> None:
    profile = JurisdictionProfile(id="idare", name="İdare", raw={})

    candidates = ForumAndDeadlineAnalyzer().analyze(
        "İdare işlemi nedeniyle hak kaybım var.",
        TemporalLegalContext.from_question("İdare işlemi nedeniyle hak kaybım var."),
        profile,
    )

    assert {candidate.kind for candidate in candidates} >= {"mahkeme", "idari_kurum"}
    assert any(candidate.assumptions for candidate in candidates)


def test_document_citation_is_attached_to_forum_candidate() -> None:
    from legalai.packages.shared.types import Document

    profile = JurisdictionProfile(id="hukuk", name="Hukuk", raw={})
    candidates = ForumAndDeadlineAnalyzer().analyze(
        "Sözleşmeden doğan alacak",
        TemporalLegalContext.from_question("Sözleşmeden doğan alacak"),
        profile,
        documents=[Document("d1", "Görev ve yetki değerlendirmesi için belge alıntısı.", "yargitay", "E. 1 K. 2")],
    )

    assert candidates[0].evidence[0].document_id == "d1"
    assert candidates[0].evidence[0].full_citation == "E. 1 K. 2"
