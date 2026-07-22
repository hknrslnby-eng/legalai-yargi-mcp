"""High-level, human-friendly installation service."""

from __future__ import annotations

from pathlib import Path

from .config_merge import merge_codex_toml_config, merge_json_config, merge_vscode_json_config
from .ides import get_ide_config
from .ides import detect_ide_configs
from .models import InstallRequest, InstallResult, McpLaunchSpec
from .paths import build_checkout_launch_spec, build_portable_launch_spec, prepare_env_file


def _default_home(home: Path | None) -> Path:
    return home if home is not None else Path.home()


def _default_appdata(appdata: Path | None) -> Path:
    return appdata if appdata is not None else Path.home() / "AppData" / "Roaming"


def _merge(config, spec: McpLaunchSpec, request: InstallRequest) -> InstallResult:
    if request.dry_run:
        return InstallResult(config.ide_id, config.path, "dry-run", None, f"{config.label}: {config.path} yazılmaya hazır.")
    if config.format == "vscode-json":
        result = merge_vscode_json_config(config.path, spec, repair=request.repair)
    elif config.format == "toml":
        result = merge_codex_toml_config(config.path, spec)
    else:
        result = merge_json_config(config.path, spec, repair=request.repair)
    return InstallResult(config.ide_id, result.config_path, result.status, result.backup_path, result.message)


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
    if request.portable_root is not None:
        prepare_env_file(request.portable_root)
    results: list[InstallResult] = []
    for ide_id in request.ide_ids:
        config = get_ide_config(ide_id, home=home, appdata=appdata, project_dir=project_dir)
        results.append(_merge(config, spec, request))
    return results


def register_all_installed_ides(
    request: InstallRequest,
    *,
    home: Path | None = None,
    appdata: Path | None = None,
    project_dir: Path | None = None,
) -> list[InstallResult]:
    """Register every supported installed client and report skipped clients."""
    home = _default_home(home)
    appdata = _default_appdata(appdata)
    project_dir = project_dir or request.install_dir
    configs = detect_ide_configs(home=home, appdata=appdata, project_dir=project_dir)
    selected = [config for config in configs if config.exists or not request.only_installed]
    install_request = InstallRequest(
        install_dir=request.install_dir,
        data_dir=request.data_dir,
        ide_ids=tuple(config.ide_id for config in selected),
        portable_root=request.portable_root,
        dry_run=request.dry_run,
        repair=request.repair,
        only_installed=request.only_installed,
    )
    installed = install_socratlegal(install_request, home=home, appdata=appdata, project_dir=project_dir)
    if request.only_installed:
        installed_ids = {result.ide_id for result in installed}
        installed.extend(
            InstallResult(config.ide_id, config.path, "skipped", None, f"{config.label} yapılandırması bulunmadı; daha sonra yeniden çalıştırılabilir.")
            for config in configs
            if config.ide_id not in installed_ids
        )
    return installed
