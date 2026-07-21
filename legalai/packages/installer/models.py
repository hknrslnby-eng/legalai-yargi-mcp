"""Data models shared by the installer and update lifecycle."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class McpLaunchSpec:
    name: str
    command: str
    args: tuple[str, ...]
    cwd: str
    env: dict[str, str] | None = None


@dataclass(frozen=True)
class InstallRequest:
    install_dir: Path
    data_dir: Path | None
    ide_ids: tuple[str, ...]
    portable_root: Path | None
    dry_run: bool = False
    repair: bool = False
    only_installed: bool = False


@dataclass(frozen=True)
class InstallResult:
    ide_id: str
    config_path: Path
    status: str
    backup_path: Path | None
    message: str
