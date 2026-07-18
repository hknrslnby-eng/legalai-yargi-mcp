import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_codex_and_cursor_configs_are_independent_stdio_records() -> None:
    codex = tomllib.loads((ROOT / ".codex" / "config.toml").read_text(encoding="utf-8"))
    cursor = json.loads((ROOT / ".cursor" / "mcp.json").read_text(encoding="utf-8"))

    codex_legalai = codex["mcp_servers"]["legalai"]
    assert codex_legalai["command"] == "uv"
    assert codex_legalai["args"] == ["run", "legalai-mcp"]
    assert codex_legalai["cwd"] == "."

    cursor_servers = cursor["mcpServers"]
    legalai = cursor_servers["legalai"]
    assert legalai["cwd"].endswith("legalai-yargi-mcp")
    assert legalai["args"] == ["-m", "legalai.apps.mcp.server"]
    assert "yargi-mcp-fork" in cursor_servers


def test_client_configs_do_not_contain_inline_api_keys() -> None:
    for path in (ROOT / ".codex" / "config.toml", ROOT / ".cursor" / "mcp.json"):
        text = path.read_text(encoding="utf-8")
        assert "OPENROUTER_API_KEY=" not in text
        assert "DEEPSEEK_API_KEY=" not in text
        assert "GEMINI_API_KEY=" not in text


def test_client_matrix_documentation_is_ide_first_and_portable() -> None:
    text = (ROOT / "docs" / "mcp-client-matrix.md").read_text(encoding="utf-8")

    for client in ("Codex", "Cursor", "Claude", "Antigravity", "VS Code"):
        assert client in text
    for marker in (
        "uv run --directory",
        "legalai_saglik_kontrolu",
        "legalai_yardim",
        "legalai://capabilities",
        "Mevcut ayarları silmeyin",
    ):
        assert marker in text
