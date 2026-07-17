from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_week11_docs_are_ide_first_and_secret_free() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    demo = (ROOT / "docs" / "week11-demo.md").read_text(encoding="utf-8")
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    combined = "\n".join((readme, demo, contributing))
    for client in ("Codex", "Cursor", "Claude", "Antigravity", "VS Code"):
        assert client in combined
    for marker in (
        "legalai_saglik_kontrolu",
        "legalai_yardim",
        "Yalın",
        "Yönlendirilmiş",
        "Rafine",
    ):
        assert marker in combined
    assert "OPENROUTER_API_KEY=" not in combined
    assert "DEEPSEEK_API_KEY=" not in combined
    assert "10000000146" not in combined
