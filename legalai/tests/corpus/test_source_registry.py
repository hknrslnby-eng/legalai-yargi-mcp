import pytest

from legalai.packages.corpus.sources.registry import SourceDescriptor, default_source_registry


def test_registry_separates_status_and_authority():
    registry = default_source_registry()

    assert registry.get("bam").status == "live_ready"
    assert registry.get("bim").status == "verification_pending"
    assert registry.get("bim").live_supported is False
    assert registry.get("oecd_competition").authority_level == "non_binding_policy_reference"


def test_default_registry_keeps_corpus_priority_separate_from_legal_authority():
    registry = default_source_registry()

    ordered = [item.source_id for item in registry.all()]

    assert ordered[:4] == [
        "eu_commission_competition",
        "eu_court_competition",
        "oecd_competition",
        "rekabet_kurumu",
    ]
    assert registry.get("yargitay").live_supported is True
    assert registry.get("yargitay").local_supported is True
    assert registry.get("bedesten").local_supported is False


def test_source_descriptor_keeps_legacy_capability_arguments_positional():
    descriptor = SourceDescriptor("legacy", "Legacy", "test", 1, False, False, {"origin": "test"})

    assert descriptor.live_supported is False
    assert descriptor.local_supported is False
    assert descriptor.metadata == {"origin": "test"}


def test_source_descriptor_requires_new_metadata_as_keywords():
    with pytest.raises(TypeError):
        SourceDescriptor("unsafe", "Unsafe", "test", 1, True, True, {}, "disabled")
