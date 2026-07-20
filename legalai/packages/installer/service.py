"""High-level, human-friendly installation service."""

from __future__ import annotations

from pathlib import Path

from .config_merge import merge_codex_toml_config, merge_json_config, merge_vscode_json_config
from .ides import get_ide_config
from .models import InstallRequest, InstallResult, McpLaunchSpec
from .paths import build_checkout_launch_spec, build_portable_launch_spec


def _default_home(home: Path | None) -> Path:
    return home if home is not None else Path.home()


def _default_appdata(appdata: Path | None) -> Path:
    return appdata if appdata is not None else Path.home() / "AppData" / "Roaming"


def _merge(config, spec: McpLaunchSpec, request: InstallRequest) -> InstallResult:
    if request.dry_run:
        return InstallResult(config.ide_id, config.path, "dry-run", None, f"{config.label}: {config.path} yazılmaya hazır.")
    if config.format == "vscode-json":
        return merge_vscode_json_config(config.path, spec, repair=request.repair)
    if config.format == "toml":
        return merge_codex_toml_config(config.path, spec)
    return merge_json_config(config.path, spec, repair=request.repair)


def install_socratlegal(
    request: InstallRequest,
    *,
    home: Path | None = None,
    appdata: Path | None = None,
    project_dir: Path | None = None,
) -> list[InstallResult]:
    """Install only into selected IDE configurations; missing files are created."""

    home = _default_home(home)
    appdata = _default_appdata(appdata)
    project_dir = project_dir or request.install_dir
    spec = (
        build_portable_launch_spec(request.portable_root)
        if request.portable_root is not None
        else build_checkout_launch_spec(request.install_dir)
    )
    results: list[InstallResult] = []
    for ide_id in request.ide_ids:
        config = get_ide_config(ide_id, home=home, appdata=appdata, project_dir=project_dir)
        results.append(_merge(config, spec, request))
    return results
