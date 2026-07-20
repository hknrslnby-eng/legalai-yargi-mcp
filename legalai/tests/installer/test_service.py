from pathlib import Path

from legalai.packages.installer.ides import detect_ide_configs
from legalai.packages.installer.models import InstallRequest
from legalai.packages.installer.service import install_socratlegal
from legalai.apps.cli.main import app
from typer.testing import CliRunner


runner = CliRunner()


def test_detect_ides_reports_known_user_and_workspace_locations(tmp_path: Path) -> None:
    home = tmp_path / "home"
    appdata = tmp_path / "appdata"
    project = tmp_path / "project"
    (home / ".cursor").mkdir(parents=True)
    (home / ".cursor" / "mcp.json").write_text("{}", encoding="utf-8")

    found = {item.ide_id: item for item in detect_ide_configs(home=home, appdata=appdata, project_dir=project)}

    assert found["cursor"].exists is True
    assert found["antigravity"].path == home / ".gemini" / "config" / "mcp_config.json"
    assert found["vscode"].path == project / ".vscode" / "mcp.json"
    assert found["claude"].path == appdata / "Claude" / "claude_desktop_config.json"
    assert found["codex"].path == home / ".codex" / "config.toml"


def test_install_creates_only_selected_ide_config(tmp_path: Path) -> None:
    home = tmp_path / "home"
    appdata = tmp_path / "appdata"
    project = tmp_path / "project"
    install_dir = tmp_path / "SocratLegal"
    request = InstallRequest(install_dir, None, ("cursor",), None)

    results = install_socratlegal(request, home=home, appdata=appdata, project_dir=project)

    assert len(results) == 1
    assert results[0].status == "installed"
    assert (home / ".cursor" / "mcp.json").exists()
    assert not (home / ".gemini" / "config" / "mcp_config.json").exists()


def test_dry_run_does_not_write_configuration(tmp_path: Path) -> None:
    request = InstallRequest(tmp_path / "SocratLegal", None, ("cursor",), None, dry_run=True)

    results = install_socratlegal(request, home=tmp_path / "home", appdata=tmp_path / "appdata", project_dir=tmp_path / "project")

    assert results[0].status == "dry-run"
    assert not (tmp_path / "home" / ".cursor" / "mcp.json").exists()


def test_cli_install_has_human_readable_dry_run(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "install",
            "--install-dir",
            str(tmp_path / "SocratLegal"),
            "--ide",
            "cursor",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "cursor" in result.stdout.lower()
    assert "dry" in result.stdout.lower()
