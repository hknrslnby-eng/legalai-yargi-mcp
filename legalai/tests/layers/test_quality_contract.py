import pytest

from legalai.packages.layers.quality_contract import (
    build_quality_contract,
    resolve_quality_profile,
)


def test_model_aliases_resolve_to_shared_frontier_quality_contract():
    profile = resolve_quality_profile("auto", "Gemini 3.1 Pro")

    assert profile.name == "frontier"
    assert profile.critic_passes >= 1


def test_quality_contract_requires_auditable_reasoning_without_hidden_chain_of_thought():
    contract = build_quality_contract("exhaustive", source_ids=("d-1", "d-2"))

    assert "Ham düşünce zincirini isteme veya ifşa etme" in contract
    assert "#d-1" in contract and "#d-2" in contract
    assert "karşı görüş" in contract
    assert "temporal context" in contract


def test_quality_contract_rejects_unknown_profile():
    with pytest.raises(ValueError):
        resolve_quality_profile("unknown")
