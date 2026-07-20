import json
from pathlib import Path

import pytest

from legalai.packages.installer.config_merge import (
    ConfigMergeError,
    merge_codex_toml_config,
    merge_json_config,
    merge_vscode_json_config,
)
from legalai.packages.installer.models import McpLaunchSpec


@pytest.fixture
def launch_spec() -> McpLaunchSpec:
    return McpLaunchSpec(
        name="socratlegal",
        command="C:/SocratLegal/runtime/uv.exe",
        args=("run", "--directory", "C:/SocratLegal/app", "socratlegal-mcp"),
        cwd="C:/SocratLegal/app",
    )


def test_json_merge_preserves_other_servers_and_is_idempotent(tmp_path: Path, launch_spec: McpLaunchSpec) -> None:
    path = tmp_path / "mcp.json"
    path.write_text(json.dumps({"mcpServers": {"existing": {"command": "node", "args": ["x"]}}}), encoding="utf-8")

    first = merge_json_config(path, launch_spec)
    second = merge_json_config(path, launch_spec)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert set(data["mcpServers"]) == {"existing", "socratlegal"}
    assert data["mcpServers"]["socratlegal"]["command"] == launch_spec.command
    assert first.status == "installed"
    assert second.status == "unchanged"
    assert second.backup_path is None


def test_json_merge_creates_backup_before_change(tmp_path: Path, launch_spec: McpLaunchSpec) -> None:
    path = tmp_path / "mcp.json"
    path.write_text('{"mcpServers": {}}', encoding="utf-8")

    result = merge_json_config(path, launch_spec, backup_dir=tmp_path / "backups")

    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert json.loads(result.backup_path.read_text(encoding="utf-8")) == {"mcpServers": {}}


def test_invalid_json_is_not_overwritten_without_repair(tmp_path: Path, launch_spec: McpLaunchSpec) -> None:
    path = tmp_path / "mcp.json"
    original = '{"mcpServers": {}}\n{"mcpServers": {"other": {}}}'
    path.write_text(original, encoding="utf-8")

    with pytest.raises(ConfigMergeError):
        merge_json_config(path, launch_spec)

    assert path.read_text(encoding="utf-8") == original


def test_repair_mode_merges_concatenated_json_objects(tmp_path: Path, launch_spec: McpLaunchSpec) -> None:
    path = tmp_path / "mcp.json"
    path.write_text('{"mcpServers": {}}\n{"mcpServers": {"other": {"command": "node"}}}', encoding="utf-8")

    result = merge_json_config(path, launch_spec, repair=True)
    data = json.loads(path.read_text(encoding="utf-8"))

    assert result.status == "installed"
    assert set(data["mcpServers"]) == {"other", "socratlegal"}


def test_vscode_merge_uses_servers_schema(tmp_path: Path, launch_spec: McpLaunchSpec) -> None:
    path = tmp_path / "mcp.json"
    path.write_text('{"servers": {"other": {"type": "stdio", "command": "node"}}}', encoding="utf-8")

    merge_vscode_json_config(path, launch_spec)
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["servers"]["other"]["command"] == "node"
    assert data["servers"]["socratlegal"]["type"] == "stdio"
    assert data["servers"]["socratlegal"]["args"] == list(launch_spec.args)


def test_codex_toml_merge_preserves_other_tables(tmp_path: Path, launch_spec: McpLaunchSpec) -> None:
    path = tmp_path / "config.toml"
    path.write_text('[mcp_servers.other]\ncommand = "node"\nargs = ["x"]\n', encoding="utf-8")

    merge_codex_toml_config(path, launch_spec)
    text = path.read_text(encoding="utf-8")

    assert "[mcp_servers.other]" in text
    assert "[mcp_servers.socratlegal]" in text
    assert 'command = "C:/SocratLegal/runtime/uv.exe"' in text
