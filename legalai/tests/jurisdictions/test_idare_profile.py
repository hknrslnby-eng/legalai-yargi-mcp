from legalai.packages.jurisdictions.loader import load_profile


def test_idare_profile_loads_with_expected_shape():
    profile = load_profile("idare")

    assert profile.id == "idare"
    assert len(profile.axes) >= 4
    assert profile.procedural_deadlines["iptal_davası"]["days"] == 60
