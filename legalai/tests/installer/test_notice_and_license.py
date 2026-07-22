from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_upstream_mit_and_fork_attribution_are_preserved() -> None:
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    notice_text = (ROOT / "NOTICE.md").read_text(encoding="utf-8")

    assert "MIT License" in license_text
    assert "Copyright (c) 2025 saidsurucu" in license_text
    assert "Copyright (c) 2026 Hakan Arslanbay" in license_text
    assert "https://github.com/saidsurucu/yargi-mcp" in notice_text
    assert "does not relicense upstream" in notice_text


def test_notice_requires_source_provenance_and_license_notes() -> None:
    text = (ROOT / "NOTICE.md").read_text(encoding="utf-8").lower()

    assert "citation" in text
    assert "retrieval date" in text
    assert "license note" in text
    assert "not an official publication" in text
