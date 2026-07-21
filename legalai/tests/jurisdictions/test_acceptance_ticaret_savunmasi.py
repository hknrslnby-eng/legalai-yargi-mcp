from legalai.packages.jurisdictions.persona import compose_persona_instructions
from legalai.packages.jurisdictions.selection import guess_jurisdictions
from legalai.packages.layers.legal_reasoning import build_reasoning_instructions


def test_trade_defense_end_to_end_persona_and_reasoning():
    selection = guess_jurisdictions(
        "İhracatçı firma için dampinge karşı vergi soruşturmasında savunma stratejisi ve GTİP itirazı hazırlanacak."
    )
    assert selection.primary == "ticaret_savunmasi"

    persona = compose_persona_instructions([selection.primary], selection.expert_lenses)
    assert "gümrük" in persona.lower() or "damping" in persona.lower()

    reasoning = build_reasoning_instructions(
        [selection.primary], source_context="trade_defense_research"
    )
    assert "4. Cevap ve strateji nedir?" in reasoning
    assert "analysis-only" in reasoning
