"""Bkz. FORK-KAPSAMLI-PLAN.md §9.7: gerçek HUDOC HTML örnekleri (kısaltılmış)
`tests/fixtures/aihm/` altında; her biri için `sections`'ın beklenen
yapıda olduğu doğrulanır."""
import pathlib

import pytest

from legalai.packages.aihm.parser import parse_sections

FIXTURES_DIR = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "aihm"
FIXTURE_FILES = sorted(FIXTURES_DIR.glob("*.txt"))


@pytest.mark.parametrize("fixture_path", FIXTURE_FILES, ids=lambda p: p.stem)
def test_parse_sections_finds_core_sections(fixture_path: pathlib.Path):
    text = fixture_path.read_text(encoding="utf-8")

    sections = parse_sections(text)

    assert "procedure" in sections
    assert "facts" in sections
    assert "law" in sections
    assert "operative" in sections
    assert sections["operative"].startswith("FOR THESE REASONS")


def test_fixtures_directory_has_at_least_three_files():
    assert len(FIXTURE_FILES) >= 3


def test_parse_sections_detects_separate_opinion_when_present():
    text = (
        "PROCEDURE lorem ipsum. THE FACTS lorem ipsum. THE LAW lorem ipsum. "
        "FOR THESE REASONS, THE COURT declares. DISSENTING OPINION OF JUDGE X "
        "I disagree with the majority."
    )

    sections = parse_sections(text)

    assert "separate" in sections
    assert sections["separate"].startswith("DISSENTING OPINION")


def test_parse_sections_missing_sections_are_absent():
    text = "Bu metinde hiçbir bölüm başlığı yok."

    sections = parse_sections(text)

    assert sections == {}
