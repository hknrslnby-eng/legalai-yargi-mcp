from legalai.packages.jurisdictions.loader import load_profile


def test_hukuk_profile_loads_with_expected_shape():
    profile = load_profile("hukuk")

    assert profile.id == "hukuk"
    assert len(profile.axes) >= 4
    assert "ispat" in profile.axes
    assert profile.procedural_deadlines["temyiz"]["days"] == 15
    assert "KARŞI OY" in profile.dissent_headers
