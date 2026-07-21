import json
from pathlib import Path

from legalai.packages.installer.models import InstallRequest
from legalai.packages.installer.service import register_all_installed_ides


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
