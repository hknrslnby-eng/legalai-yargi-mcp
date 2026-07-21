from legalai.packages.jurisdictions.loader import load_profile
from legalai.packages.jurisdictions.persona import compose_persona_instructions


def test_reklam_kurulu_persona_contains_legal_consumer_board_and_sector_lenses():
    profile = load_profile("reklam_kurulu")
    assert {"reklam_hukuku", "tuketici_hukuku", "reklamcilik_sektoru"} <= set(profile.expert_lenses)
    prompt = compose_persona_instructions(["reklam_kurulu", "hukuk"])
    assert "Reklam Kurulu" in prompt
    assert "reklamcılık sektörü" in prompt
