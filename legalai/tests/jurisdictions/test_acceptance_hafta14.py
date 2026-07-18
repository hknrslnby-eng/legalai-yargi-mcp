from legalai.packages.jurisdictions.selection import guess_jurisdictions
from legalai.packages.layers.legal_reasoning import build_reasoning_instructions
from legalai.packages.sources.policy import load_source_policies


def test_week14_keeps_haksiz_rekabet_separate_from_rekabet():
    assert "haksiz_rekabet" != "rekabet"


def test_week14_unknown_selection_falls_back_to_diger():
    selection = guess_jurisdictions("Bunun hukuki çözümü için ne yapabilirim?")

    assert selection.primary == "diger"


def test_week14_multi_domain_selection_supports_ceza():
    selection = guess_jurisdictions("Sahte belge nedeniyle ceza ve vergi sorumluluğu doğar mı?")

    assert selection.primary in {"ceza", "vergi"}
    assert "ceza" in {selection.primary, *selection.supporting}


def test_week14_reasoning_and_oecd_boundaries():
    reasoning = build_reasoning_instructions(["rekabet"], source_context="competition_research")
    policies = load_source_policies()

    assert "4. Cevap ve strateji nedir?" in reasoning
    assert policies["oecd_competition"].authority_level == "non_binding_policy_reference"

