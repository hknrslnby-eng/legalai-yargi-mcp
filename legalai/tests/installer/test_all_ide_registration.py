import json
import tomllib
from pathlib import Path

from legalai.packages.installer.models import InstallRequest
from legalai.packages.installer.service import install_socratlegal, register_all_installed_ides


def test_all_registration_detects_existing_clients_preserves_unrelated_servers_and_is_idempotent(tmp_path: Path):
    home = tmp_path / "home"
    appdata = tmp_path / "appdata"
    project = tmp_path / "project"
    cursor = home / ".cursor" / "mcp.json"
    cursor.parent.mkdir(parents=True)
    cursor.write_text(json.dumps({"mcpServers": {"other": {"command": "node"}}}), encoding="utf-8")
    request = InstallRequest(project, None, ("all",), None, only_installed=True)

    first = register_all_installed_ides(request, home=home, appdata=appdata, project_dir=project)
    installed = next(item for item in first if item.ide_id == "cursor")
    assert installed.status == "installed"
    assert any(item.ide_id == "codex" and item.status == "skipped" for item in first)
    payload = json.loads(cursor.read_text(encoding="utf-8"))
    assert "other" in payload["mcpServers"]
    assert "socratlegal" in payload["mcpServers"]
    assert installed.backup_path is not None and installed.backup_path.exists()

    second = register_all_installed_ides(request, home=home, appdata=appdata, project_dir=project)
    assert next(item for item in second if item.ide_id == "cursor").status == "unchanged"


def test_only_installed_can_be_disabled_for_explicit_all_selection(tmp_path: Path):
    project = tmp_path / "project"
    request = InstallRequest(project, None, ("all",), None, only_installed=False)
    results = register_all_installed_ides(request, home=tmp_path / "home", appdata=tmp_path / "appdata", project_dir=project)
    assert {item.ide_id for item in results} == {"cursor", "antigravity", "vscode", "claude", "codex"}


def test_explicit_all_writes_each_supported_client_schema_and_is_idempotent(tmp_path: Path) -> None:
    home = tmp_path / "home"
    appdata = tmp_path / "appdata"
    project = tmp_path / "project"
    bundle = tmp_path / "portable"
    (bundle / "app").mkdir(parents=True)
    (bundle / "app" / "legalai.env.example").write_text("OPENAI_API_KEY=\n", encoding="utf-8")
    (home / ".cursor").mkdir(parents=True)
    (home / ".cursor" / "mcp.json").write_text(
        json.dumps({"mcpServers": {"existing": {"command": "node"}}}),
        encoding="utf-8",
    )
    (home / ".codex").mkdir(parents=True)
    (home / ".codex" / "config.toml").write_text(
        '[mcp_servers.existing]\ncommand = "node"\n',
        encoding="utf-8",
    )
    request = InstallRequest(
        install_dir=project,
        data_dir=None,
        ide_ids=("cursor", "antigravity", "vscode", "claude", "codex"),
        portable_root=bundle,
    )

    first = install_socratlegal(request, home=home, appdata=appdata, project_dir=project)
    assert {item.ide_id for item in first} == {"cursor", "antigravity", "vscode", "claude", "codex"}

    cursor = json.loads((home / ".cursor" / "mcp.json").read_text(encoding="utf-8"))
    antigravity = json.loads((home / ".gemini" / "config" / "mcp_config.json").read_text(encoding="utf-8"))
    vscode = json.loads((project / ".vscode" / "mcp.json").read_text(encoding="utf-8"))
    claude = json.loads((appdata / "Claude" / "claude_desktop_config.json").read_text(encoding="utf-8"))
    codex = tomllib.loads((home / ".codex" / "config.toml").read_text(encoding="utf-8"))

    assert "existing" in cursor["mcpServers"]
    assert cursor["mcpServers"]["socratlegal"]["env"]["SOCRATLEGAL_ENV_FILE"].endswith("portable\\config\\.env")
    assert antigravity["mcpServers"]["socratlegal"]["cwd"].endswith("portable\\app")
    assert vscode["servers"]["socratlegal"]["type"] == "stdio"
    assert claude["mcpServers"]["socratlegal"]["command"].endswith("runtime\\uv.exe")
    assert "existing" in codex["mcp_servers"]
    assert codex["mcp_servers"]["socratlegal"]["env"]["SOCRATLEGAL_ENV_FILE"].endswith("portable\\config\\.env")

    second = install_socratlegal(request, home=home, appdata=appdata, project_dir=project)
    assert {item.status for item in second} == {"unchanged"}
