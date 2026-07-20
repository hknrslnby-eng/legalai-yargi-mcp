from legalai.packages.corpus.sources.registry import default_source_registry


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
