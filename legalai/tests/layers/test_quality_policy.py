from legalai.packages.layers.operational_context import OperationalContextBuilder
from legalai.packages.layers.quality_policy import build_quality_context


def test_build_quality_context_includes_non_override_policy_labels_and_source_limits():
    operational_context = OperationalContextBuilder().build(
        "Kripto cüzdanına yönlendirildim ve verilerim paylaşıldı",
        ["ceza", "kvkk"],
    )

    context = build_quality_context(
        jurisdiction_ids=["ceza", "kvkk"],
        expert_lenses=["ticaret"],
        source_ids=["doc-1", "doc-2"],
        operational_context=operational_context,
        quality_profile="exhaustive",
        model_hint="Codex frontier",
    )

    assert "System and safety rules remain highest priority." in context
    assert "cannot be overridden by a generic model prompt, a simple domain persona, or Superpowers" in context
    assert "Jurisdictions/personas: ceza, kvkk." in context
    assert "Expert lenses: ticaret." in context
    assert "Allowed operational labels" in context
    assert "operasyonel hipotez" in context
    assert "Source limit" in context
    assert "#doc-1" in context and "#doc-2" in context
    assert "analysis_only=true" in context
    assert "non_binding=true" in context

