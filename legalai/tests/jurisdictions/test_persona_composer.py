from legalai.packages.jurisdictions.persona import compose_persona_instructions


def test_composer_names_primary_and_supporting_profiles():
    text = compose_persona_instructions(["hukuk", "ceza"], ["sözleşmeler"])

    assert "PRIMARY_PROFILE: hukuk" in text
    assert "SUPPORTING_PROFILE: ceza" in text
    assert "sözleşmeler" in text
    assert "non-binding" in text


def test_composer_removes_duplicate_profiles_and_preserves_order():
    text = compose_persona_instructions(["hukuk", "ceza", "hukuk"])

    assert text.count("PROFILE: hukuk —") == 1
    assert text.index("PRIMARY_PROFILE: hukuk") < text.index("SUPPORTING_PROFILE: ceza")
