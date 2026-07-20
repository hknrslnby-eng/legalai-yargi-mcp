from pathlib import Path


ROOT = Path(__file__).parents[3]


def test_user_install_doc_is_portable_first_and_describes_updates() -> None:
    text = (ROOT / "docs" / "socratlegal-user-install.md").read_text(encoding="utf-8")
    assert "portable paket" in text.lower()
    assert "Python, uv veya GitHub CLI" in text
    assert "app.previous" in text
    assert "bilirkişi raporu" in text.lower()


def test_docs_do_not_call_expert_report_flow_planned() -> None:
    text = (ROOT / "docs" / "mcp-client-setup.md").read_text(encoding="utf-8").lower()
    assert "henuz uretim modulu degildir" not in text
