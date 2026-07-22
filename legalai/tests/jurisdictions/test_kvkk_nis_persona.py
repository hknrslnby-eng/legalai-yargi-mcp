from legalai.packages.jurisdictions.loader import load_profile
from legalai.packages.jurisdictions.persona import compose_persona_instructions
from legalai.packages.jurisdictions.selection import guess_jurisdictions


def test_kvkk_profile_exposes_nis_and_cyber_lenses_without_unconditional_criminal_admin():
    profile = load_profile("kvkk")

    assert {"nis_1", "nis_2", "siber_guvenlik"} <= set(profile.expert_lenses)
    assert profile.related_law_domains["conditional"] == ["idare", "ceza", "sozlesmeler", "is_hukuku", "tazminat"]
    assert set(profile.comparative_lenses) == {"nis_1", "nis_2"}
    assert "idare" not in profile.expert_lenses
    assert "ceza" not in profile.expert_lenses


def test_kvkk_selection_adds_contextual_lenses_and_persona_guardrail():
    selection = guess_jurisdictions("Vendor veri ihlali; employee erisimi, contract ve idari bildirim sorunu.")

    assert selection.primary == "kvkk"
    assert {"nis_1", "nis_2", "siber_guvenlik", "idare", "sozlesmeler", "is_hukuku"} <= set(selection.related_law.supporting)
    assert any("idari" in reason for reason in selection.related_law.reasons)
    persona = compose_persona_instructions(["kvkk"], selection.expert_lenses)
    assert "nis_1" in persona
    assert "RELATED_LAW_RULE" in persona
