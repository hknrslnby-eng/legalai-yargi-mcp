"""Known local MCP configuration locations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IdeConfig:
    ide_id: str
    label: str
    path: Path
    format: str
    exists: bool


IdeDescriptor = IdeConfig


def discover_supported_ides(*, home: Path, appdata: Path, project_dir: Path) -> tuple[IdeDescriptor, ...]:
    """Return all supported clients and whether their config currently exists."""
    return detect_ide_configs(home=home, appdata=appdata, project_dir=project_dir)


def detect_ide_configs(*, home: Path, appdata: Path, project_dir: Path) -> tuple[IdeConfig, ...]:
    candidates = (
        ("cursor", "Cursor", home / ".cursor" / "mcp.json", "json"),
        ("antigravity", "Antigravity", home / ".gemini" / "config" / "mcp_config.json", "json"),
        ("vscode", "VS Code workspace", project_dir / ".vscode" / "mcp.json", "vscode-json"),
        ("claude", "Claude Desktop", appdata / "Claude" / "claude_desktop_config.json", "json"),
        ("codex", "Codex", home / ".codex" / "config.toml", "toml"),
    )
    return tuple(IdeConfig(ide_id, label, path, fmt, path.exists()) for ide_id, label, path, fmt in candidates)


def get_ide_config(ide_id: str, *, home: Path, appdata: Path, project_dir: Path) -> IdeConfig:
    for config in detect_ide_configs(home=home, appdata=appdata, project_dir=project_dir):
        if config.ide_id == ide_id:
            return config
    raise KeyError(f"Bilinmeyen IDE: {ide_id}")
