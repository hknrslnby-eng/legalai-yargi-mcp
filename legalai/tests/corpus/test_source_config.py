from pathlib import Path

import pytest
import yaml

from legalai.packages.corpus.sources.registry import (
    default_source_registry,
    load_source_metadata,
    validate_source_metadata,
)

SOURCE_CONFIG_DIR = Path(__file__).parents[2] / "configs" / "sources"


def _sources(filename: str) -> list[dict[str, object]]:
    data = yaml.safe_load((SOURCE_CONFIG_DIR / filename).read_text(encoding="utf-8"))
    return list(data["sources"])


def test_live_source_configs_carry_authority_and_usage_metadata():
    sources = _sources("competition.yaml") + _sources("institutions.yaml")

    for source in sources:
        assert source["source_kind"]
        assert source["authority_level"]
        assert source["allowed_contexts"]
        assert source["full_text_storage"] in {"allowed", "metadata_or_excerpt_only"}
        assert source["publisher_class"]
        assert source["license_note"]


def test_reports_are_economic_support_not_precedent():
    reports = _sources("reports.yaml")

    assert {source["source_id"] for source in reports} == {"competition_reports", "institution_reports"}
    assert all(source["source_kind"].endswith("report") for source in reports)
    assert all(source["precedential"] is False for source in reports)
    assert all(source["authority_level"] == "non_binding_economic_reference" for source in reports)


def test_authority_registry_families_are_configured():
    source_ids = {
        source["source_id"]
        for filename in ("competition.yaml", "institutions.yaml")
        for source in _sources(filename)
    }

    assert {"bam", "bim", "idare_mahkemeleri", "danistay", "dg_comp", "curia", "oecd_competition"} <= source_ids


def test_source_configs_match_registry_authority_status_and_contexts():
    validate_source_metadata(default_source_registry(), load_source_metadata(SOURCE_CONFIG_DIR))


def test_source_metadata_validation_rejects_registry_drift():
    source = _sources("institutions.yaml")[0] | {"authority_level": "mismatched"}

    with pytest.raises(ValueError, match="authority_level"):
        validate_source_metadata(default_source_registry(), [source])
