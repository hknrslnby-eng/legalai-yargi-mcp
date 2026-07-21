from legalai.packages.petitions.models import PetitionRequest
from legalai.packages.petitions.service import process_petition


def test_draft_is_source_grounded_and_exposes_turkish_language_lens():
    result = process_petition(
        PetitionRequest(
            operation="draft",
            petition_text=None,
            question="Kira alacağının tahsili için dava dilekçesi hazırla.",
            party_position="davacı",
            jurisdiction_hint="hukuk/kira",
        )
    )
    assert result.operation == "draft"
    assert result.analysis_only and result.non_binding
    assert result.quality["turkish_language_professor_lens"] is True
    assert result.source_requirements["citation_and_quote_required"] is True
    assert any(section["id"] == "talep_sonucu" for section in result.sections)
    assert result.cross_domain_inquiry["detected_domains"]


def test_review_classifies_procedural_paragraphs_and_duplicates():
    result = process_petition(
        PetitionRequest(
            operation="review",
            petition_text=(
                "Dava şartı ve görev itirazlarımız saklıdır.\n"
                "Olay 1 gerçekleşmiştir.\n"
                "Olay 1 gerçekleşmiştir.\n"
                "SONUÇ VE İSTEM: Davanın kabulü."
            ),
            question="Dilekçeyi incele.",
        )
    )
    assert any(item["classification"] == "risky_or_procedural" for item in result.paragraphs)
    assert any(item["classification"] == "duplicative" for item in result.paragraphs)
    assert result.protected_topics >= {"dava şartı", "görev", "talep sonucu"}


def test_shorten_proposes_but_does_not_silently_delete_protected_content():
    result = process_petition(
        PetitionRequest(
            operation="shorten",
            petition_text="Dava şartı vardır. Olayın kısa özeti budur. SONUÇ VE İSTEM: Kabul.",
            question="Dilekçeyi kısalt.",
        )
    )
    assert result.protected_topics
    assert result.shortening_safeguards["requires_user_confirmation"] is True
    assert all(item["action"] != "delete" for item in result.changes if item["paragraph_index"] in {1, 3})


def test_lengthen_requires_sources_and_rejects_new_facts():
    result = process_petition(
        PetitionRequest(
            operation="lengthen",
            petition_text="Talebimiz kabul edilmelidir.",
            question="Kaynaklı olarak geliştir; yeni vakıa ekleme.",
            source_documents=[{"id": "doc-1", "citation": "Kaynak künyesi", "quote": "Kısa alıntı"}],
        )
    )
    assert result.lengthening_safeguards["new_facts_allowed"] is False
    assert result.source_requirements["allowed_source_ids"] == ["doc-1"]
    assert "Türkçe" in result.quality["language_instruction"]


def test_party_position_changes_the_quality_contract():
    claimant = process_petition(PetitionRequest(operation="draft", petition_text=None, question="Alacak", party_position="davacı"))
    respondent = process_petition(PetitionRequest(operation="draft", petition_text=None, question="Alacak", party_position="davalı"))
    assert claimant.quality["party_position"] == "davacı"
    assert respondent.quality["party_position"] == "davalı"
    assert claimant.quality["party_position_instruction"] != respondent.quality["party_position_instruction"]
