from legalai.packages.jurisdictions.loader import load_profile


def test_ceza_profile_loads_with_expected_shape():
    profile = load_profile("ceza")

    assert profile.id == "ceza"
    assert len(profile.axes) >= 4
    assert "kast_taksir" in profile.axes
    assert profile.procedural_deadlines["temyiz"]["days"] == 15
    assert profile.evidence_standard == "şüpheden sanık yararlanır (in dubio pro reo)"
