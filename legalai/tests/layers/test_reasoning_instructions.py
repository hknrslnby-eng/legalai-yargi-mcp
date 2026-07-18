from legalai.packages.layers.legal_reasoning import build_reasoning_instructions


def test_reasoning_instructions_contain_four_ordered_steps():
    text = build_reasoning_instructions(["hukuk", "ceza"])
    positions = [text.index(marker) for marker in (
        "1. Hukuki sorun nedir?",
        "2. Teorik ve yasal altyapı nedir?",
        "3. Somut olayın unsurlarla ilişkisi nedir?",
        "4. Cevap ve strateji nedir?",
    )]
    assert positions == sorted(positions)
    assert "Temporal Legal Context" in text
    assert "karşıt görüş" in text


def test_reasoning_instructions_cover_procedural_and_source_boundaries():
    text = build_reasoning_instructions(["rekabet"], source_context="competition_research")

    assert "zamanaşımı" in text
    assert "hak düşürücü süre" in text
    assert "görev" in text and "yetki" in text
    assert "non-binding" in text
    assert "OECD" in text
    assert "analysis-only" in text

