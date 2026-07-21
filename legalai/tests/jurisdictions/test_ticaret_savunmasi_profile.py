from legalai.packages.jurisdictions.loader import load_profile


def test_ticaret_savunmasi_profile_loads_with_expected_shape():
    profile = load_profile("ticaret_savunmasi")

    assert profile.id == "ticaret_savunmasi"
    assert len(profile.axes) >= 4
    assert "damping_marji" in profile.axes
    assert "gumruk_hukuku" in profile.expert_lenses
    assert profile.disclaimer_required is True
    assert profile.system_prompt_persona.startswith("Kıdemli")
