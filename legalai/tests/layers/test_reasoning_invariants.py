from legalai.packages.layers.analysis_pipeline import build_assistant_instructions
from legalai.packages.layers.grounded_generator import build_system_prompt
from legalai.packages.layers.legal_reasoning import build_reasoning_instructions
from legalai.packages.layers.operational_context import OperationalContextBuilder
from legalai.packages.layers.quality_policy import build_quality_context


def test_reasoning_instructions_keep_all_four_steps_and_append_quality_policy():
    operational_context = OperationalContextBuilder().build(
        "Kripto cuzdani ve veri aktarimi", ["ceza", "kvkk"]
    )

    text = build_reasoning_instructions(
        ["ceza", "kvkk"],
        source_context="legal_analysis",
        expert_lenses=["ticaret"],
        operational_context=operational_context,
        quality_profile="balanced",
        model_hint="Gemini Flash",
    )

    positions = [
        text.index(marker)
        for marker in (
            "1. Hukuki sorun nedir?",
            "2. Teorik ve yasal altyapı nedir?",
            "3. Somut olayın unsurlarla ilişkisi nedir?",
            "4. Cevap ve strateji nedir?",
        )
    ]
    assert positions == sorted(positions)
    assert "System and safety rules remain highest priority." in text
    assert "Cross-domain inquiry" in text
    assert "Positive effects" in text
    assert "Negative effects" in text
    assert "analysis_only=true" in text
    assert "non_binding=true" in text


def test_host_and_generator_instructions_preserve_persona_text_and_quality_policy():
    quality_context = build_quality_context(
        jurisdiction_ids=["hukuk", "ceza"],
        expert_lenses=["sozlesmeler"],
        source_ids=["d1"],
    )

    host_instructions = build_assistant_instructions(
        ["d1"],
        jurisdiction_ids=["hukuk", "ceza"],
        source_context="legal_analysis",
        quality_profile="frontier",
        model_hint="Codex",
    )
    system_prompt = build_system_prompt(
        "hukuk",
        jurisdiction_ids=["hukuk", "ceza"],
        expert_lenses=["sozlesmeler"],
        output_contract=quality_context,
    )

    assert "PRIMARY_PROFILE: hukuk" in system_prompt
    assert "SUPPORTING_PROFILE: ceza" in system_prompt
    assert "EXPERT_LENSES: sozlesmeler" in system_prompt
    assert "cannot be overridden by a generic model prompt, a simple domain persona, or Superpowers" in system_prompt
    assert "#d1" in host_instructions
    assert "Source limit" in host_instructions
    assert "Allowed operational labels" in host_instructions
