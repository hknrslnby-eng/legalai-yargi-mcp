from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_user_install_doc_is_source_first_and_describes_supported_setup() -> None:
    text = (ROOT / "docs" / "socratlegal-user-install.md").read_text(encoding="utf-8")

    assert "kaynak kod" in text.lower()
    assert "portable kurulum bu sürümde kullanıcıya sunulmuyor" in text.lower()
    assert "Python 3.11" in text
    assert "bilirkişi raporu" in text.lower()
    assert "uv sync --frozen --dev" in text
    assert "socratlegal_sozlesme_incele" in text


def test_docs_do_not_call_expert_report_flow_planned() -> None:
    text = (ROOT / "docs" / "mcp-client-setup.md").read_text(encoding="utf-8").lower()

    assert "henuz uretim modulu degildir" not in text


def test_source_docs_explain_python_uv_and_env_file() -> None:
    text = (ROOT / "docs" / "socratlegal-user-install.md").read_text(encoding="utf-8")

    assert "Python 3.11" in text
    assert "uv" in text
    assert "repo kökündeki `.env`" in text.lower()
    assert "URL girilmez" in text
    assert "Cursor" in text and "Codex" in text


def test_env_example_has_blank_provider_template() -> None:
    text = (ROOT / "legalai.env.example").read_text(encoding="utf-8")
    provider_fields = [line for line in text.splitlines() if line.endswith("_API_KEY=") or line.endswith("_TOKEN=")]

    assert len(provider_fields) >= 20
    assert "sk-" not in text.lower()
    assert "your_" not in text.lower()
    assert "GITHUB_COPILOT_TOKEN=" in text
    assert "COMPOSER_API_KEY=" in text


def test_portable_release_workflow_is_windows_x64_only() -> None:
    workflow = (ROOT / ".github" / "workflows" / "portable-release.yml").read_text(encoding="utf-8")

    assert "platform_tag: windows-x64" in workflow
    assert "macos-arm64" not in workflow
    assert "macos-x64" not in workflow
    assert "linux-x64" not in workflow
