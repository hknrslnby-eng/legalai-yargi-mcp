from legalai.packages.jurisdictions.loader import load_profile


def test_aym_profile_loads_with_expected_shape():
    profile = load_profile("aym")

    assert profile.id == "aym"
    assert len(profile.axes) >= 4
    assert profile.procedural_deadlines["bireysel_basvuru_süresi"]["days"] == 30
    assert "bireysel_basvuru" in profile.raw.get("basvuru_turleri", [])
    assert profile.raw.get("connectors", [{}])[0].get("jurisdiction") == "aihm"
