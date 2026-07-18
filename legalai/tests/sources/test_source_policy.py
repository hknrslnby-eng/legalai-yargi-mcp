from legalai.packages.sources.policy import load_source_policies, policies_for_context


def test_oecd_is_competition_research_only_by_default():
    policies = policies_for_context("competition_research")
    oecd = next(item for item in policies if item.source_id == "oecd_competition")

    assert oecd.authority_level == "non_binding_policy_reference"


def test_oecd_is_not_default_legal_analysis_source():
    assert all(item.source_id != "oecd_competition" for item in policies_for_context("legal_analysis"))


def test_public_doctrine_requires_citation_and_license_metadata():
    policies = load_source_policies()
    doctrine = policies["dergipark_and_open_doctrine"]

    assert doctrine.citation_required is True
    assert doctrine.full_text_storage in {"allowed", "metadata_or_excerpt_only"}


def test_requested_doctrine_sources_are_catalogued():
    policies = load_source_policies()

    assert {
        "baro_and_tbb_journals",
        "yok_public_law_theses",
        "rekabet_authority_expert_theses",
        "rekabet_journal",
    }.issubset(policies)
